"""Invalid definitions preserve plain path evidence rather than masking it."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures


class InvalidDefinitions(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def test_empty_label_keeps_uncertain_plain_path_and_exact_span(self):
        target = self.put(self.root / 'docs/setup.md', 'Potential instructions.')
        for label in (' ', '\t', '\r\n', ' \t\n '):
            with self.subTest(label=label):
                text = f'Read [{label}].\n\n[{label}]: docs/setup.md\n'
                self.put(self.source, text)
                graph = self.build()
                self.assertEqual(len(graph['occurrences']), 1)
                row = graph['occurrences'][0]
                self.assertEqual((row['syntax'], row['classification'], row['status'], row['targets']),
                                 ('plain', 'uncertain', 'unresolved', []))
                self.assertEqual(text[slice(*row['span'])], 'docs/setup.md')
                self.assertTrue(graph['partial'])
                self.assertFalse(graph['text_read_complete'])
                self.assertFalse(any(str(target) in n['aliases'] for n in graph['nodes'].values()))

    def test_read_prose_in_invalid_definition_remains_dependency(self):
        leaf = self.put(self.root / 'docs/leaf.md', 'Leaf policy.')
        self.put(self.root / 'docs/setup.md', 'Read [leaf](leaf.md).\n')
        self.put(self.source, '[ ]: Read docs/setup.md before editing.\n')
        graph = self.build(bases={str(self.source): {'kind': 'document_dir'}})
        self.assertEqual({r['terminal_path'] for r in self.routes(graph)}, {str(leaf)})
        self.assertFalse(graph['partial'])

    def test_empty_use_without_path_and_fenced_invalid_definition_controls(self):
        for text in ('Read [ ].\n', '```text\n[ ]: docs/setup.md\n```\n'):
            with self.subTest(text=text):
                self.put(self.source, text)
                graph = self.build()
                self.assertEqual(graph['occurrences'], [])
                self.assertFalse(graph['partial'])
