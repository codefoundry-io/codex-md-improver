"""Recursive-glob limits, resolution coverage and URI inventory controls."""
from pathlib import Path
import sys
import unittest

PROJECT = Path('/Users/chaniri/codex_workspace/workspace/codex-md-improver')
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures


class ReferenceBoundaries(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    decision = fixtures.ReferenceTests.decision

    def tree(self):
        return [self.put(self.root / name, 'healthy text') for name in
                ('docs/index.md', 'docs/a/x.md', 'docs/a/b/y.md')]

    def test_globstar_is_an_explicit_unresolved_boundary(self):
        paths = self.tree()
        for target in ('docs/**/*.md', 'docs/**', str(self.root / 'docs/**/*.md')):
            with self.subTest(target=target):
                self.put(self.source, f'Read [notes]({target}).\n')
                graph = self.build()
                occurrence = graph['occurrences'][0]
                self.assertEqual(occurrence['status'], 'unresolved')
                self.assertEqual(occurrence['targets'], [])
                self.assertTrue(graph['partial'])
                self.assertFalse(graph['text_read_complete'])
                self.assertTrue(all(r['lower_bound'] for r in self.routes(graph)))
                aliases = {p for n in graph['nodes'].values() for p in n['aliases']}
                self.assertFalse(aliases.intersection(map(str, paths)))

    def test_plain_globstar_and_unchanged_resolution_remain_unresolved(self):
        self.tree()
        self.put(self.source, 'Read `docs/**/*.md`.\n')
        for resolutions in ([], [self.decision('docs/**/*.md', target='docs/**/*.md')]):
            with self.subTest(resolved=bool(resolutions)):
                graph = self.build(bases={str(self.source): {'kind': 'document_dir'}}, resolutions=resolutions)
                self.assertEqual(graph['occurrences'][0]['status'], 'unresolved')
                self.assertTrue(graph['partial'])

    def test_ordinary_globs_and_explicit_replacement_controls(self):
        top, nested, _ = self.tree()
        for target, expected in [('docs/*.md', top), ('docs/*/*.md', nested), ('docs/ab**/*.md', None)]:
            if expected is None:
                expected = self.put(self.root / 'docs/abc/z.md', 'z')
            with self.subTest(target=target):
                self.put(self.source, f'Read [notes]({target}).\n')
                graph = self.build()
                self.assertFalse(graph['partial'])
                self.assertEqual([r['terminal_path'] for r in self.routes(graph)], [str(expected)])
        self.put(self.source, 'Read [notes](docs/**/*.md).\n')
        for target in ('docs/index.md', 'docs/'):
            graph = self.build(resolutions=[self.decision('docs/**/*.md', target=target)])
            self.assertFalse(graph['partial'])
        graph = self.build(resolutions=[self.decision('docs/**/*.md', 'informational')])
        self.assertFalse(graph['partial'])

    def test_literal_globstar_base_is_not_an_operator(self):
        folder = self.root / '**'
        target = self.put(folder / 'only.md', 'only')
        self.put(self.source, 'Read `*.md`.\n')
        graph = self.build(bases={str(self.source): {'kind': 'absolute', 'path': str(folder)}})
        self.assertFalse(graph['partial'])
        self.assertEqual([r['terminal_path'] for r in self.routes(graph)], [str(target)])
        self.put(self.source, 'Read [notes](${PROJECT_ROOT}/*.md).\n')
        chain = self.chain()
        chain['scenario_project_root'] = str(folder)
        graph = self.build([chain])
        self.assertFalse(graph['partial'])
        self.assertEqual([r['terminal_path'] for r in self.routes(graph)], [str(target)])

    def test_unscoped_and_scoped_overlap_is_rejected_in_both_orders(self):
        self.put(self.source, 'Maybe `guide.md`.\n')
        self.put(self.root / 'guide.md', 'guide')
        unscoped = self.decision('guide.md', target='guide.md', base={'kind': 'document_dir'})
        chains = [self.chain(scenario='a'), self.chain(scenario='b')]
        for classification in ('informational', 'read_dependency'):
            scoped = self.decision('guide.md', classification, scenario_id='a')
            for records in ([unscoped, scoped], [scoped, unscoped]):
                with self.subTest(classification=classification, scoped_first='scenario_id' in records[0]):
                    with self.assertRaises(ValueError):
                        self.build(chains, resolutions=records)

    def test_disjoint_scopes_and_one_unscoped_control(self):
        self.put(self.source, 'Maybe `guide.md`.\n')
        self.put(self.root / 'guide.md', 'guide')
        chains = [self.chain(scenario='a'), self.chain(scenario='b')]
        decisions = [self.decision('guide.md', 'informational', scenario_id=s) for s in ('a', 'b')]
        self.assertFalse(self.build(chains, resolutions=decisions)['partial'])
        self.assertFalse(self.build(chains, resolutions=[self.decision('guide.md', 'informational')])['partial'])

    def test_file_uri_inventory_and_explicit_local_resolution_controls(self):
        target = self.put(self.root / 'linked.md', 'Read [nested](nested.md).\n')
        leaf = self.put(self.root / 'nested.md', 'leaf')
        for uri in (target.as_uri(), 'file://other-host/path', 'file:relative.md', 'https://example.org/a'):
            with self.subTest(uri=uri):
                self.put(self.source, f'Read [notes]({uri}).\n')
                graph = self.build()
                self.assertEqual(graph['occurrences'][0]['status'], 'url')
                self.assertFalse(graph['partial'])
                self.assertFalse(any(str(target) in n['aliases'] for n in graph['nodes'].values()))
        uri = target.as_uri()
        self.put(self.source, f'Read [notes]({uri}).\n')
        graph = self.build(resolutions=[self.decision(uri, target=str(target))])
        self.assertFalse(graph['partial'])
        self.assertEqual([r['terminal_path'] for r in self.routes(graph)], [str(leaf)])
