"""Reference uses bind to the first accepted matching definition."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures


class DefinitionPrecedence(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def tree(self):
        self.required = self.put(self.root / 'required.md', 'Read [nested](nested.md).\n')
        self.nested = self.put(self.root / 'nested.md', 'Required nested policy.')
        self.decoy = self.put(self.root / 'decoy.md', 'Readable decoy.')

    def check_required(self, graph):
        rows = self.routes(graph)
        self.assertEqual([r['terminal_path'] for r in rows], [str(self.nested)])
        self.assertEqual(rows[0]['route_original_bytes'],
                         sum(p.stat().st_size for p in (self.source, self.required, self.nested)))
        self.assertFalse(rows[0]['lower_bound'])
        self.assertFalse(graph['partial'])
        self.assertTrue(graph['text_read_complete'])
        self.assertFalse(any(str(self.decoy) in node['aliases'] for node in graph['nodes'].values()))

    def test_full_collapsed_and_shortcut_links_choose_first_definition(self):
        self.tree()
        for use in ('[policy][rules]', '[rules][]', '[rules]'):
            with self.subTest(use=use):
                self.put(self.source, f'Read {use}.\n\n[rules]: required.md\n[rules]: decoy.md\n')
                self.check_required(self.build())

    def test_casefolded_duplicate_and_usage_after_definitions(self):
        self.tree()
        self.put(self.source, '[Rules]: required.md "first title"\n[RULES]: decoy.md\n\nRead [policy][rules].\n')
        self.check_required(self.build())

    def test_missing_first_target_is_not_masked_by_readable_later_target(self):
        self.tree()
        self.required.unlink()
        self.put(self.source, 'Read [policy][rules].\n\n[rules]: required.md\n[rules]: decoy.md\n')
        graph = self.build()
        self.assertTrue(graph['partial'])
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(self.required), 'missing_target')])

    def test_fenced_definition_does_not_win(self):
        self.tree()
        self.put(self.source, '```text\n[rules]: decoy.md\n```\n\n'
                              '[rules]: required.md\n\nRead [policy][rules].\n')
        self.check_required(self.build())

    def test_distinct_labels_and_identical_duplicate_control(self):
        self.tree()
        self.put(self.source, '[rules]: required.md\n[rules]: required.md\n[other]: decoy.md\n\nRead [rules].\n')
        self.check_required(self.build())
