"""Minor review findings with observable coverage consequences."""
import hashlib
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures


class ParserContracts(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    decision = fixtures.ReferenceTests.decision

    def test_label_with_spaces_is_not_nonlocal_and_can_be_resolved(self):
        for label, target in (('Spec: docs/spec.md', 'docs/spec.md'),
                              ('include: .github/workflows/ci.yml', '.github/workflows/ci.yml')):
            with self.subTest(label=label):
                leaf = self.put(self.root / target, 'evidence')
                self.put(self.source, 'Before editing, consult `' + label + '`.\n')
                graph = self.build()
                self.assertNotEqual(graph['occurrences'][0]['status'], 'url')
                self.assertTrue(graph['partial'])
                graph = self.build(resolutions=[self.decision(label, target=target,
                                                             base={'kind': 'document_dir'})])
                self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})
                self.assertFalse(graph['partial'])

    def test_valid_uri_and_filename_line_control(self):
        self.put(self.root / 'guide.md', 'guide')
        for target in ('https://example.org:443/a%20b', 'tel:123', 'custom:123',
                       'mailto:help@example.com', 'guide.md:12'):
            with self.subTest(target=target):
                self.put(self.source, 'Read [' + target + '](' + target + ').\n')
                graph = self.build()
                self.assertFalse(graph['partial'])
                self.assertEqual(graph['occurrences'][0]['status'],
                                 'resolved' if target == 'guide.md:12' else 'url')

    def test_dotfile_configs_are_leaves_except_explicit_resolution(self):
        config_dir = self.root / 'deploy'
        paths = [self.put(config_dir / name, 'FAKE_VALUE=https://example.org/fake\n'
                          'Read [dependency](missing.md).\n') for name in ('.env', '.npmrc', '.pgpass')]
        self.put(self.source, 'Read [deployment](deploy/).\n')
        graph = self.build()
        self.assertFalse([e for e in graph['occurrences'] if e['source'] in map(str, paths)])
        self.assertFalse(graph['partial'])
        leaf = self.put(config_dir / 'chosen.md', 'chosen evidence')
        path = paths[0]
        text = path.read_text()
        start = text.index('missing.md')
        resolution = {'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'span': [start, start + len('missing.md')], 'text': 'missing.md',
                      'classification': 'read_dependency', 'target': 'chosen.md',
                      'base': {'kind': 'document_dir'}}
        graph = self.build(resolutions=[resolution])
        edges = [e for e in graph['occurrences'] if e['source'] in map(str, paths)]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]['targets'], [str(leaf)])

    def test_selected_guidance_and_linked_extensionless_controls(self):
        leaf = self.put(self.root / 'rules.md', 'rules')
        for name in ('INSTRUCTIONS', '.cursorrules', '.env'):
            with self.subTest(selected=name):
                source = self.put(self.root / name, 'Read [rules](rules.md).\n')
                graph = self.build([self.chain(source=source)])
                self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})
        for name in ('CONVENTIONS', '.cursorrules'):
            with self.subTest(linked=name):
                self.put(self.root / name, 'Read [rules](rules.md).\n')
                self.put(self.source, 'Read [rules](' + name + ').\n')
                graph = self.build()
                self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})

    def test_invalid_reference_definition_prose_remains_extractable(self):
        leaf = self.put(self.root / 'docs/unique.md', 'unique')
        setup = self.put(self.root / 'docs/setup.md', 'Read [unique](unique.md).\n')
        for separator in (' ', '\n'):
            with self.subTest(separator=separator):
                self.put(self.source, '[Important]:' + separator + 'Read docs/setup.md before editing.\n')
                graph = self.build(bases={str(self.source): {'kind': 'document_dir'}})
                self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})
                self.assertFalse(graph['partial'])
                setup.unlink()
                missing = self.build(bases={str(self.source): {'kind': 'document_dir'}})
                self.assertTrue(missing['partial'])
                self.assertTrue(any(r['terminal_kind'] == 'missing_target' for r in self.routes(missing)))
                self.put(setup, 'Read [unique](unique.md).\n')

    def test_valid_definition_destinations_and_titles_control(self):
        leaf = self.put(self.root / 'guide.md', 'guide')
        for target in ('guide.md', '<guide.md>'):
            for title in ('', ' "title fake.md"', " 'title fake.md'", ' (title fake.md)'):
                for separator in (' ', '\n'):
                    with self.subTest(target=target, title=title, separator=separator):
                        self.put(self.source, 'Read [g] and [guide][g].\n\n[g]:' + separator + target + title + '\n')
                        graph = self.build()
                        self.assertFalse(graph['partial'])
                        self.assertEqual([e['target_text'] for e in graph['occurrences']], ['guide.md', 'guide.md'])
                        self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})
