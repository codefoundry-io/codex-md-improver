"""The SKILL basename boundary applies to files, not arbitrary filesystem kinds."""
import os
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures


class SkillBoundaryKind(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def test_skill_named_directory_traverses_ordinary_descendant(self):
        guide = self.put(self.root / 'SKILL.md/guide.md', 'Ordinary readable guide.')
        self.put(self.source, 'Read [manual](SKILL.md/).\n')
        graph = self.build()
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(guide), 'leaf')])
        self.assertFalse(graph['partial'])
        self.assertTrue(graph['text_read_complete'])

    def test_skill_named_fifo_stays_special_file_frontier(self):
        fifo = self.root / 'SKILL.md'
        os.mkfifo(fifo)
        self.put(self.source, 'Read [special](SKILL.md).\n')
        graph = self.build()
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(fifo), 'special_file')])
        self.assertTrue(graph['partial'])
        self.assertFalse(graph['text_read_complete'])

    def test_regular_skill_file_remains_excluded(self):
        skill = self.put(self.root / 'SKILL.md', 'Existing skill content.')
        self.put(self.source, 'Read [skill](SKILL.md).\n')
        graph = self.build()
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(skill), 'excluded_skill')])
        self.assertFalse(any(str(skill) in n['aliases'] for n in graph['nodes'].values()))

    def test_named_directory_containing_skill_file_remains_excluded(self):
        folder = self.root / 'SKILL.md'
        self.put(folder / 'SKILL.md', 'Existing skill content.')
        self.put(folder / 'guide.md', 'Excluded directory sibling.')
        self.put(self.source, 'Read [skill](SKILL.md/).\n')
        graph = self.build()
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(folder), 'excluded_skill')])
