"""Filesystem traversal, route uncertainty and resolution input contracts."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
from discovery import _Content
from references import _identity, build_reference_graph


class R5Contracts(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    cli = fixtures.ReferenceTests.cli

    def linked_fixture(self, symlink=True):
        self.put(self.root / 'a/guide.md', 'Read [wrong](wrong.md).\n')
        self.put(self.root / 'a/wrong.md', 'decoy')
        self.put(self.root / 'b/guide.md', 'Read [unique](unique.md).\n')
        self.put(self.root / 'b/unique.md', 'intended')
        (self.root / 'b/deep').mkdir()
        if symlink:
            (self.root / 'a/link').symlink_to('../b/deep', target_is_directory=True)
        else:
            (self.root / 'a/link').mkdir()
        return self.root / 'a/link/../guide.md'

    def test_dependency_preserves_symlink_parent_traversal(self):
        alias = self.linked_fixture()
        real_guide, real_leaf = self.root / 'b/guide.md', self.root / 'b/unique.md'
        decoy_ids = {_identity((self.root / 'a' / name).stat()) for name in ('guide.md', 'wrong.md')}
        for absolute in (False, True):
            for syntax in ('markdown', 'plain'):
                target = str(alias) if absolute else 'a/link/../guide.md'
                text = f'Read [guide]({target}).\n' if syntax == 'markdown' else f'Read `{target}`.\n'
                with self.subTest(absolute=absolute, syntax=syntax):
                    self.put(self.source, text)
                    read_paths = []
                    original = _Content.read
                    def read(content, path):
                        read_paths.append(Path(path))
                        return original(content, path)
                    with patch.object(_Content, 'read', read):
                        graph = self.build(bases={str(self.source): {'kind': 'document_dir'}})
                    self.assertIn(_identity(real_guide.stat()), graph['nodes'])
                    self.assertIn(_identity(real_leaf.stat()), graph['nodes'])
                    self.assertFalse(decoy_ids & graph['nodes'].keys())
                    self.assertFalse(decoy_ids & {_identity(p.stat()) for p in read_paths})
                    self.assertIn(str(alias), graph['nodes'][_identity(real_guide.stat())]['aliases'])
                    self.assertTrue(any(e['source'] == str(alias) and e['target_text'] == 'unique.md'
                                        for e in graph['occurrences']))
                    self.assertFalse(graph['partial'])

    def test_glob_preserves_symlink_parent_traversal(self):
        self.linked_fixture()
        self.put(self.source, 'Read [guides](a/link/../*.md).\n')
        graph = self.build()
        ids = graph['nodes'].keys()
        for name in ('guide.md', 'unique.md'):
            with self.subTest(intended=name):
                self.assertIn(_identity((self.root / 'b' / name).stat()), ids)
        for name in ('guide.md', 'wrong.md'):
            with self.subTest(decoy=name):
                self.assertNotIn(_identity((self.root / 'a' / name).stat()), ids)
        self.assertTrue(any(e['source'] == str(self.root / 'a/link/../guide.md')
                            and e['target_text'] == 'unique.md' for e in graph['occurrences']))

    def test_selected_source_alias_binds_semantic_resolution(self):
        alias = self.linked_fixture()
        self.put(self.root / 'b/guide.md', 'Read handbook.\n')
        text = alias.read_text()
        start = text.index('handbook')
        resolution = {'source': str(alias), 'source_sha256': hashlib.sha256(alias.read_bytes()).hexdigest(),
                      'span': [start, start + 8], 'text': 'handbook', 'classification': 'read_dependency',
                      'target': 'unique.md', 'base': {'kind': 'document_dir'}}
        try:
            graph = self.build([self.chain(source=alias)], resolutions=[resolution])
        except ValueError as exc:
            self.fail('The exact selected alias must remain usable for resolution: ' + str(exc))
        self.assertIn(_identity((self.root / 'b/unique.md').stat()), graph['nodes'])
        self.assertEqual(graph['occurrences'][0]['source'], str(alias))

    def test_real_directory_parent_control(self):
        self.linked_fixture(symlink=False)
        self.put(self.source, 'Read [guide](a/link/../guide.md).\n')
        graph = self.build()
        self.assertIn(_identity((self.root / 'a/wrong.md').stat()), graph['nodes'])
        self.assertNotIn(_identity((self.root / 'b/unique.md').stat()), graph['nodes'])
        self.assertFalse(graph['partial'])

    def test_invalid_intermediate_components_do_not_collapse_to_existing_target(self):
        decoy = self.put(self.root / 'guide.md', 'decoy')
        self.put(self.root / 'file', 'not a directory')
        for intermediate in ('missing', 'file'):
            for glob in (False, True):
                with self.subTest(intermediate=intermediate, glob=glob):
                    target = '*.md' if glob else 'guide.md'
                    self.put(self.source, f'Read [guide]({intermediate}/../{target}).\n')
                    graph = self.build()
                    self.assertNotIn(_identity(decoy.stat()), graph['nodes'])
                    self.assertTrue(graph['partial'])

    def test_failed_loader_prefix_makes_healthy_leaf_total_a_lower_bound(self):
        blocked = self.put(self.root / 'ancestor.md', 'unreadable instructions')
        leaf = self.put(self.root / 'leaf.md', 'leaf')
        for global_source in (False, True):
            for reference_leaf in (False, True):
                with self.subTest(global_source=global_source, reference_leaf=reference_leaf):
                    self.put(self.source, 'Read [leaf](leaf.md).\n' if reference_leaf else 'child instructions')
                    chain = self.chain(global_path=blocked if global_source else None)
                    if not global_source:
                        chain['sources'].insert(0, {'path': str(blocked), 'original_bytes': blocked.stat().st_size})
                    original = _Content.read
                    def read(content, path):
                        if Path(path) == blocked:
                            raise PermissionError('synthetic loader read denial')
                        return original(content, path)
                    with patch.object(_Content, 'read', read):
                        graph = self.build([chain])
                    target = leaf if reference_leaf else self.source
                    row = next(r for r in self.routes(graph) if r['terminal_path'] == str(target))
                    self.assertEqual(row['terminal_kind'], 'leaf')
                    self.assertEqual(row['content_status'], 'read')
                    self.assertTrue(row['lower_bound'])
                    self.assertEqual(row['route_original_bytes'], self.source.stat().st_size +
                                     (leaf.stat().st_size if reference_leaf else 0))
                    self.assertTrue(graph['partial'])
                    self.assertTrue(any(r['terminal_path'] == str(blocked) and r['lower_bound']
                                        for r in self.routes(graph)))

    def test_unrelated_reference_failure_does_not_taint_healthy_route_control(self):
        leaf = self.put(self.root / 'leaf.md', 'leaf')
        self.put(self.source, 'Read [leaf](leaf.md) and [missing](missing.md).\n')
        graph = self.build()
        rows = self.routes(graph)
        self.assertTrue(graph['partial'])
        self.assertFalse(next(r for r in rows if r['terminal_path'] == str(leaf))['lower_bound'])
        self.assertTrue(next(r for r in rows if r['terminal_kind'] == 'missing_target')['lower_bound'])

    def test_falsey_nonlist_resolutions_rejected_by_api(self):
        for value in ({}, False, 0, ''):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'Resolutions must be a list'):
                    build_reference_graph([self.chain()], resolutions=value,
                                          context={'user_home': self.home, 'codex_home': self.home})

    def test_optional_api_resolutions_control(self):
        for kwargs in ({}, {'resolutions': None}, {'resolutions': []}):
            with self.subTest(kwargs=kwargs):
                graph = build_reference_graph([self.chain()], **kwargs,
                                              context={'user_home': self.home, 'codex_home': self.home})
                self.assertFalse(graph['partial'])

    def test_explicit_cli_nonarray_resolutions_rejected_before_output(self):
        for index, value in enumerate(({}, False, 0, '', None)):
            with self.subTest(value=value):
                input_path = self.put(self.base / f'resolutions-{index}.json', json.dumps(value))
                result, out = self.cli(['--resolutions', str(input_path)])
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn('Resolutions must be a list', result.stderr)
                self.assertFalse(out.exists())

    def test_cli_omitted_or_empty_array_control(self):
        empty = self.put(self.base / 'resolutions-empty.json', '[]')
        for extra in ([], ['--resolutions', str(empty)]):
            with self.subTest(extra=extra):
                result, out = self.cli(extra)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((out / 'audit.json').is_file())
