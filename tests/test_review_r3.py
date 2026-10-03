"""R3 concrete parser and configuration-boundary counterexamples."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_discovery as discovery_fixtures
import test_references as reference_fixtures
from discovery import _Content, resolve_settings, scan
import md_improver


class MarkdownReview(unittest.TestCase):
    setUp = reference_fixtures.ReferenceTests.setUp
    put = reference_fixtures.ReferenceTests.put
    chain = reference_fixtures.ReferenceTests.chain
    build = reference_fixtures.ReferenceTests.build
    routes = reference_fixtures.ReferenceTests.routes

    def test_fences_preserve_outside_links_and_exclude_inside_links(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        self.put(self.root / 'hidden.md', 'inside example')
        tick = chr(96)
        cases = ((tick * 4, tick * 3 + 'python', tick * 4),
                 (tick * 3, '~~~', tick * 3),
                 (tick * 3, tick * 3 + 'python', tick * 3))
        for opening, inner, closing in cases:
            with self.subTest(opening=opening, inner=inner):
                self.put(self.source, '\n'.join((opening, inner, '[hidden](hidden.md)',
                                               closing, 'Read [guide](guide.md).', '')))
                graph = self.build()
                self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})
                self.assertFalse(graph['partial'])
                self.assertEqual([e['target_text'] for e in graph['occurrences']], ['guide.md'])

    def test_titled_reference_definitions_resolve_full_and_shortcut_uses(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        for title in ('"Guide title"', "'Guide title'", '(Guide title)'):
            for use in ('[guide][g]', '[g]'):
                with self.subTest(title=title, use=use):
                    self.put(self.source, 'Read ' + use + '.\n\n[g]: guide.md ' + title + '\n')
                    graph = self.build()
                    self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})
                    self.assertFalse(graph['partial'])
                    self.assertEqual(graph['occurrences'][0]['target_text'], 'guide.md')
                    span = graph['occurrences'][0]['span']
                    self.assertEqual(self.source.read_text()[span[0]:span[1]], use)

    def test_line_suffix_and_fragment_keep_the_local_filename(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        for target in ('guide.md:12#section', 'guide.md:12:4#section'):
            with self.subTest(target=target):
                self.put(self.source, '[guide](' + target + ')\n')
                graph = self.build()
                self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})
                self.assertFalse(graph['partial'])


class ConfigBoundaryReview(unittest.TestCase):
    setUp = discovery_fixtures.DiscoveryTests.setUp
    put = discovery_fixtures.DiscoveryTests.put
    request = discovery_fixtures.DiscoveryTests.request

    def protected_config(self, layer, alias):
        secret = self.put(self.home / 'auth.json',
                          'project_doc_max_bytes = 7\nsentinel = "SYNTHETIC_SECRET_ONLY"\n')
        config = self.home / 'config.toml' if layer == 'global' else self.root / '.codex/config.toml'
        config.parent.mkdir(parents=True, exist_ok=True)
        config.unlink(missing_ok=True)
        if alias == 'symlink':
            config.symlink_to(secret)
        else:
            os.link(secret, config)
        return secret, config

    def guarded_read(self, secret):
        real_read = Path.read_bytes
        identity = (secret.stat().st_dev, secret.stat().st_ino)
        def read(path):
            info = path.stat()
            self.assertNotEqual((info.st_dev, info.st_ino), identity,
                                'protected fixture reached byte-read boundary')
            return real_read(path)
        return read

    def cases(self):
        for layer in ('global', 'project'):
            for alias in ('symlink', 'hardlink'):
                yield layer, alias

    def check_settings(self, value, layer):
        self.assertIsNone(value['limit'])
        self.assertIsNone(value['fallback_names'])
        self.assertIn(('user_config' if layer == 'global' else 'project_config') + ':PermissionError',
                      value['unresolved'])
        if layer == 'project':
            self.assertEqual(value['trust'], 'trusted')
            self.assertEqual(value['root_markers'], ['.git'])
        self.assertNotIn('SYNTHETIC_SECRET_ONLY', json.dumps(value))

    def test_direct_settings_never_reads_protected_config_aliases(self):
        for layer, alias in self.cases():
            with self.subTest(layer=layer, alias=alias):
                secret, config = self.protected_config(layer, alias)
                try:
                    request = self.request({'trust': {str(self.root): 'trusted'}})
                    with patch.object(Path, 'home', return_value=self.base), \
                         patch.object(Path, 'read_bytes', self.guarded_read(secret)):
                        value = asdict(resolve_settings(request, self.root))
                    self.check_settings(value, layer)
                finally:
                    config.unlink()

    def test_scan_preserves_usable_guidance_without_reading_protected_aliases(self):
        for layer, alias in self.cases():
            with self.subTest(layer=layer, alias=alias):
                secret, config = self.protected_config(layer, alias)
                content = _Content()
                try:
                    request = self.request({'trust': {str(self.root): 'trusted'}}, cwd=self.root)
                    with patch.object(Path, 'home', return_value=self.base), \
                         patch.object(Path, 'read_bytes', self.guarded_read(secret)):
                        value = scan(request, content=content)
                    self.assertEqual(value['exit_code'], 3)
                    self.assertTrue(value['partial'])
                    row = value['chains'][0]
                    self.assertTrue(any(s['sha256'] for s in [*row['sources'], *row['scope_sources']]))
                    self.check_settings(value['chains'][0]['settings'], layer)
                    self.assertFalse(any(b'SYNTHETIC_SECRET_ONLY' in data for _, data in content.cache.values()))
                finally:
                    config.unlink()

    def test_cli_config_aliases_keep_partial_artifacts_without_secret_reads(self):
        settings = self.put(self.base / 'settings.json', json.dumps({'trust': {str(self.root): 'trusted'}}))
        for index, (layer, alias) in enumerate(self.cases()):
            with self.subTest(layer=layer, alias=alias):
                secret, config = self.protected_config(layer, alias)
                out = self.base / ('out-' + str(index))
                try:
                    with patch.object(Path, 'home', return_value=self.base), \
                         patch.object(Path, 'read_bytes', self.guarded_read(secret)):
                        result = md_improver.main(['scan', '--project', str(self.root),
                            '--cwd', str(self.root), '--codex-home', str(self.home),
                            '--settings', str(settings), '--out', str(out)])
                    self.assertEqual(result, 3)
                    self.assertTrue((out / 'manifest.json').exists())
                    report = json.loads((out / 'audit.json').read_text())
                    self.check_settings(report['chains'][0]['settings'], layer)
                    self.assertTrue(report['partial'])
                    for artifact in out.iterdir():
                        if artifact.is_file():
                            self.assertNotIn('SYNTHETIC_SECRET_ONLY', artifact.read_text())
                finally:
                    config.unlink()

    def test_regular_configs_keep_existing_precedence(self):
        self.put(self.home / 'config.toml', 'project_doc_max_bytes = 80\n')
        self.put(self.root / '.codex/config.toml', 'project_doc_max_bytes = 70\n')
        request = self.request({'trust': {str(self.root): 'trusted'}})
        with patch.object(Path, 'home', return_value=self.base):
            value = resolve_settings(request, self.root)
        self.assertEqual(value.limit, 70)
        self.assertEqual(value.unresolved, [])


class AdditionalRuntimeReview(unittest.TestCase):
    setUp = reference_fixtures.ReferenceTests.setUp
    put = reference_fixtures.ReferenceTests.put
    chain = reference_fixtures.ReferenceTests.chain
    build = reference_fixtures.ReferenceTests.build
    routes = reference_fixtures.ReferenceTests.routes
    decision = reference_fixtures.ReferenceTests.decision

    def test_output_verbs_cannot_silently_discard_potential_read_dependencies(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        for line in ('Create a changeset as described in [guide](guide.md).',
                     'Write tests using [guide](guide.md).',
                     'Use [guide](guide.md) to generate clients.',
                     'Example: [guide](guide.md).'):
            with self.subTest(line=line):
                self.put(self.source, line + '\n')
                graph = self.build()
                self.assertTrue(graph['partial'])
                self.assertEqual(graph['occurrences'][0]['status'], 'unresolved')
                self.assertEqual(graph['occurrences'][0]['classification'], 'uncertain')
                resolved = self.build(resolutions=[self.decision('guide.md')])
                self.assertFalse(resolved['partial'])
                self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(resolved)})
        self.put(self.source, 'Write [report](result.md).\n')
        resolved = self.build(resolutions=[self.decision('result.md', classification='output')])
        self.assertFalse(resolved['partial'])
        self.assertEqual(resolved['occurrences'][0]['status'], 'non_read')

    def test_literal_base_magic_does_not_change_relative_path_or_glob(self):
        renamed = self.root.parent / '[archive]'
        self.root.rename(renamed)
        self.root = renamed
        self.source = self.root / 'AGENTS.md'
        leaf = self.put(self.root / 'docs/a.md', 'guide')
        for target in ('docs/a.md', 'docs/*.md'):
            with self.subTest(target=target):
                self.put(self.source, '[guide](' + target + ')\n')
                graph = self.build()
                self.assertFalse(graph['partial'])
                self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})

    def test_repeated_signal_during_receipt_does_not_escape(self):
        import signal
        saved = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
        original_write = md_improver._write_json
        for name in ('audit.json', 'manifest.json'):
            with self.subTest(receipt=name):
                out = self.base / ('signal-' + name)
                def first(*args, **kwargs):
                    signal.getsignal(signal.SIGINT)(signal.SIGINT, None)
                def second(path, value):
                    if path.name == name and (value.get('interruption') or value.get('phase') == 'interrupted'):
                        handler = signal.getsignal(signal.SIGTERM)
                        if callable(handler):
                            handler(signal.SIGTERM, None)
                    return original_write(path, value)
                try:
                    with patch('discovery.scan', first), patch.object(md_improver, '_write_json', second):
                        result = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                            '--codex-home', str(self.home), '--out', str(out)])
                except md_improver.ScanInterrupted:
                    self.fail('second handled signal escaped the receipt writer')
                self.assertEqual(result, 3)
                audit = json.loads((out / 'audit.json').read_text())
                manifest = json.loads((out / 'manifest.json').read_text())
                self.assertTrue(audit['partial'])
                self.assertEqual(audit['exit_code'], 3)
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['phase'], 'interrupted')
                self.assertEqual({sig: signal.getsignal(sig) for sig in saved}, saved)

    def test_early_interrupt_is_best_effort_and_does_not_create_unvalidated_output(self):
        out = self.base / 'early-interrupt'
        with patch('discovery.validate_request', side_effect=KeyboardInterrupt):
            result = md_improver.main(['scan', '--project', str(self.root),
                                      '--codex-home', str(self.home), '--out', str(out)])
        self.assertEqual(result, 3)
        self.assertFalse(out.exists())


class ScopePathReview(unittest.TestCase):
    setUp = discovery_fixtures.DiscoveryTests.setUp
    put = discovery_fixtures.DiscoveryTests.put
    request = discovery_fixtures.DiscoveryTests.request

    def test_parent_components_are_rejected_before_scope_checks(self):
        outside = self.base / 'outside'
        self.put(outside / 'AGENTS.md', 'outside')
        lexical = self.root / '..' / 'outside'
        cases = (
            self.request(cwd=lexical),
            self.request(projects=[self.root / '..' / 'project']),
            self.request({'environment_groups': [{'id': 'bad', 'cwds': [str(lexical)]}]}),
        )
        from discovery import validate_request
        for request in cases:
            with self.subTest(request=request):
                with self.assertRaises(ValueError):
                    validate_request(request)


if __name__ == '__main__':
    unittest.main()
