"""Overlapping title links must not erase outside semantic context."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures


class InlineOverlapReview(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def test_nested_title_links_preserve_outside_example_context(self):
        self.put(self.root / 'guide.md', 'guide')
        self.put(self.root / 'fake.md', 'title only')
        for delimiter in ('"', "'"):
            with self.subTest(delimiter=delimiter):
                self.put(self.source, 'Read [guide](guide.md ' + delimiter +
                         '[nested](fake.md)' + delimiter + ') Example.\n')
                graph = self.build()
                self.assertEqual([e['target_text'] for e in graph['occurrences']], ['guide.md'])
                self.assertEqual(graph['occurrences'][0]['classification'], 'uncertain')
                self.assertEqual(graph['occurrences'][0]['status'], 'unresolved')
                self.assertTrue(graph['partial'])

    def test_adjacent_nonoverlapping_links_preserve_both_dependencies(self):
        one = self.put(self.root / 'one.md', 'one')
        two = self.put(self.root / 'two.md', 'two')
        self.put(self.source, 'Read [one](one.md) and [two](two.md).\n')
        graph = self.build()
        self.assertEqual([e['target_text'] for e in graph['occurrences']], ['one.md', 'two.md'])
        paths = {r['terminal_path'] for r in self.routes(graph)}
        self.assertTrue({str(one), str(two)} <= paths)
        self.assertFalse(graph['partial'])
