"""Plain filesystem targets stay literal; original Markdown destinations decode."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures


class PercentPathResolution(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    decision = fixtures.ReferenceTests.decision

    def tree(self):
        self.literal = self.put(self.root / 'notes%20policy.md', 'Read [intended](intended.md).\n')
        self.decoy = self.put(self.root / 'notes policy.md', 'Read [wrong](wrong.md).\n')
        self.intended = self.put(self.root / 'intended.md', 'intended dependency')
        self.wrong = self.put(self.root / 'wrong.md', 'wrong dependency')

    def check(self, graph, literal=True):
        first, leaf = (self.literal, self.intended) if literal else (self.decoy, self.wrong)
        omitted = (self.decoy, self.wrong) if literal else (self.literal, self.intended)
        root = next(row for row in graph['occurrences'] if row['source'] == str(self.source))
        self.assertEqual(root['targets'], [str(first)])
        aliases = {p for node in graph['nodes'].values() for p in node['aliases']}
        self.assertTrue({str(first), str(leaf)} <= aliases)
        self.assertFalse(set(map(str, omitted)) & aliases)
        routes = self.routes(graph)
        self.assertEqual([row['terminal_path'] for row in routes], [str(leaf)])
        self.assertFalse(graph['partial'])
        self.assertTrue(graph['text_read_complete'])
        self.assertFalse(routes[0]['lower_bound'])

    def test_plain_relative_absolute_and_suffix_paths_preserve_percent(self):
        self.tree()
        for target in ('notes%20policy.md', str(self.literal), 'notes%20policy.md:12#part'):
            with self.subTest(target=target):
                self.put(self.source, f'Read `{target}`.\n')
                self.check(self.build(bases={str(self.source): {'kind': 'document_dir'}}))

    def test_explicit_absolute_target_overrides_markdown_uri_literally(self):
        self.tree()
        uri = self.literal.as_uri()
        self.put(self.source, f'Read [notes]({uri}).\n')
        self.check(self.build(resolutions=[self.decision(uri, target=str(self.literal))]))

    def test_explicit_semantic_absolute_and_relative_targets_are_literal(self):
        self.tree()
        for target in (str(self.literal), 'notes%20policy.md'):
            with self.subTest(target=target):
                self.put(self.source, 'Consult the handbook.\n')
                self.check(self.build(resolutions=[self.decision('the handbook', target=target,
                                                                 base={'kind': 'document_dir'})]))

    def test_explicit_relative_markdown_target_keeps_document_base(self):
        self.tree()
        cwd = self.root / 'other'
        cwd.mkdir()
        self.put(self.source, 'Read [notes](missing.md).\n')
        self.check(self.build([self.chain(cwd=cwd)], resolutions=[self.decision('missing.md', target='notes%20policy.md')]))

    def test_original_markdown_destinations_still_decode_once(self):
        self.tree()
        for text, literal in [
                ('Read [notes](notes%20policy.md).\n', False),
                ('Read [notes][n].\n[n]: notes%20policy.md\n', False),
                ('Read [n].\n[n]: notes%20policy.md\n', False),
                ('Read [notes](notes%2520policy.md).\n', True),
                ('Read [notes](notes%20policy.md:12:4#part).\n', False)]:
            with self.subTest(text=text):
                self.put(self.source, text)
                self.check(self.build(), literal=literal)

    def test_decision_without_target_keeps_markdown_decoding(self):
        self.tree()
        self.put(self.source, 'Read [notes](notes%20policy.md).\n')
        self.check(self.build(resolutions=[self.decision('notes%20policy.md', base={'kind': 'document_dir'})]), literal=False)

    def test_file_uri_inventory_and_ordinary_absolute_target_controls(self):
        self.tree()
        uri = self.literal.as_uri()
        self.put(self.source, f'Read [notes]({uri}).\n')
        graph = self.build()
        self.assertEqual(graph['occurrences'][0]['status'], 'url')
        self.assertFalse(graph['partial'])
        graph = self.build(resolutions=[self.decision(uri, target=str(self.decoy))])
        self.check(graph, literal=False)

    def test_encoded_hash_in_markdown_filename_is_not_a_fragment(self):
        target = self.put(self.root / 'notes#part.md', 'healthy')
        self.put(self.source, 'Read [notes](notes%23part.md#section).\n')
        graph = self.build()
        self.assertEqual([row['terminal_path'] for row in self.routes(graph)], [str(target)])
        self.assertFalse(graph['partial'])
