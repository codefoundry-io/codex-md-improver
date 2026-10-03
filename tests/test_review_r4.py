"""R4 known-sensitive metadata, special configuration and inline-link cases."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_discovery as discovery_fixtures
import test_references as reference_fixtures
from discovery import _Content, ScopeRequest, resolve_settings, scan


class ReadBoundaryReview(unittest.TestCase):
    setUp = discovery_fixtures.DiscoveryTests.setUp
    put = discovery_fixtures.DiscoveryTests.put
    request = discovery_fixtures.DiscoveryTests.request

    def guarded_read(self, secret=None):
        original = Path.read_bytes
        identity = None if secret is None else (secret.stat().st_dev, secret.stat().st_ino)
        def read(path):
            info = path.stat()
            self.assertTrue(stat.S_ISREG(info.st_mode), 'special file reached byte-read boundary')
            self.assertNotEqual((info.st_dev, info.st_ino), identity,
                                'protected metadata reached byte-read boundary')
            return original(path)
        return read

    def test_inventory_rejects_protected_git_pointer_before_bytes(self):
        storage = self.base / 'git-storage'
        (self.root / '.git').rename(storage)
        secret = self.put(self.home / 'auth.json', 'gitdir: ' + str(storage) + '\n')
        os.link(secret, self.root / '.git')
        content = _Content()
        with patch.object(Path, 'home', return_value=self.base), \
             patch.object(Path, 'read_bytes', self.guarded_read(secret)):
            value = scan(self.request({'trust': {str(self.root): 'trusted'}}, cwd=self.root), content=content)
        self.assertTrue(value['partial'])
        self.assertEqual(value['exit_code'], 3)
        self.assertTrue(any(s['sha256'] for row in value['chains']
                            for s in [*row['sources'], *row['scope_sources']]))
        self.assertFalse(any(data.startswith(b'gitdir:') for _, data in content.cache.values()))

    def test_trust_lookup_rejects_each_protected_worktree_metadata_slot(self):
        for slot in ('pointer', 'gitdir', 'commondir'):
            with self.subTest(slot=slot):
                main = self.base / slot / 'main'
                linked = self.base / slot / 'linked'
                admin = main / '.git/worktrees/linked'
                self.put(main / '.git/HEAD', 'ref: refs/heads/main\n')
                self.put(linked / '.git', 'gitdir: ' + str(admin) + '\n')
                self.put(admin / 'gitdir', str(linked / '.git') + '\n')
                self.put(admin / 'commondir', '../..\n')
                target = linked / '.git' if slot == 'pointer' else admin / slot
                secret = self.put(self.home / 'auth.json', target.read_bytes())
                target.unlink()
                os.link(secret, target)
                request = ScopeRequest([linked], self.home, linked, {'trust': {str(main): 'trusted'}})
                with patch.object(Path, 'home', return_value=self.base), \
                     patch.object(Path, 'read_bytes', self.guarded_read(secret)):
                    value = asdict(resolve_settings(request, linked))
                self.assertEqual(value['trust'], 'unknown')
                self.assertIn('trust:PermissionError', value['unresolved'])
                target.unlink()

    def test_fifo_configurations_remain_partial_without_opening_them(self):
        for layer in ('global', 'project'):
            for alias in ('direct', 'symlink'):
                for entrypoint in ('settings', 'scan'):
                    with self.subTest(layer=layer, alias=alias, entrypoint=entrypoint):
                        config = self.home / 'config.toml' if layer == 'global' else self.root / '.codex/config.toml'
                        config.parent.mkdir(parents=True, exist_ok=True)
                        fifo = config if alias == 'direct' else self.base / 'config-fifo'
                        os.mkfifo(fifo)
                        if alias == 'symlink':
                            config.symlink_to(fifo)
                        try:
                            request = self.request({'trust': {str(self.root): 'trusted'}}, cwd=self.root)
                            with patch.object(Path, 'home', return_value=self.base), \
                                 patch.object(Path, 'read_bytes', self.guarded_read()):
                                if entrypoint == 'settings':
                                    value = asdict(resolve_settings(request, self.root))
                                else:
                                    report = scan(request)
                                    self.assertEqual(report['exit_code'], 3)
                                    self.assertTrue(report['partial'])
                                    row = report['chains'][0]
                                    self.assertTrue(any(s['sha256'] for s in [*row['sources'], *row['scope_sources']]))
                                    value = row['settings']
                            prefix = 'user_config:' if layer == 'global' else 'project_config:'
                            self.assertTrue(any(item.startswith(prefix) for item in value['unresolved']))
                            self.assertIsNone(value['limit'])
                        finally:
                            config.unlink()
                            if alias == 'symlink':
                                fifo.unlink()

    def test_protected_reader_rejects_all_nonregular_modes_before_bytes(self):
        target = self.put(self.base / 'mode-sentinel', 'not a real device')
        actual = target.stat()
        for mode in (stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFDIR):
            with self.subTest(mode=mode):
                fields = list(actual)
                fields[0] = mode | 0o600
                mocked = os.stat_result(fields)
                with patch.object(Path, 'stat', return_value=mocked), \
                     patch.object(Path, 'read_bytes', side_effect=AssertionError('nonregular byte read')):
                    with self.assertRaises(OSError):
                        _Content().read(target)


class InlineTitleReview(unittest.TestCase):
    setUp = reference_fixtures.ReferenceTests.setUp
    put = reference_fixtures.ReferenceTests.put
    chain = reference_fixtures.ReferenceTests.chain
    build = reference_fixtures.ReferenceTests.build
    routes = reference_fixtures.ReferenceTests.routes

    def test_inline_destinations_are_separate_from_all_title_delimiters(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        for destination in ('guide.md', '<guide.md>'):
            for title in ('"Guide title"', "'Guide title'", '(Guide title)'):
                with self.subTest(destination=destination, title=title):
                    text = 'Read [guide](' + destination + ' ' + title + ').\n'
                    self.put(self.source, text)
                    graph = self.build()
                    self.assertEqual([e['target_text'] for e in graph['occurrences']], ['guide.md'])
                    self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})
                    self.assertFalse(graph['partial'])
                    start, end = graph['occurrences'][0]['span']
                    self.assertEqual(text[start:end], 'guide.md')

    def test_inline_title_and_literal_decoy_never_replace_intended_file(self):
        guide = self.put(self.root / 'guide.md', 'intended')
        decoy = self.put(self.root / '<guide.md>', 'wrong file')
        self.put(self.source, 'Read [guide](<guide.md> "fake.md").\n')
        graph = self.build()
        paths = {r['terminal_path'] for r in self.routes(graph)}
        self.assertIn(str(guide), paths)
        self.assertNotIn(str(decoy), paths)
        self.assertEqual(len(graph['occurrences']), 1)
        self.assertFalse(graph['partial'])

    def test_untitled_angle_spaces_and_ordinary_title_control(self):
        for destination, title, name in (('<guide with spaces.md>', '', 'guide with spaces.md'),
                                        ('guide.md', ' "Guide title"', 'guide.md')):
            with self.subTest(destination=destination):
                guide = self.put(self.root / name, 'guide')
                self.put(self.source, 'Read [guide](' + destination + title + ').\n')
                graph = self.build()
                self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})
                self.assertFalse(graph['partial'])
