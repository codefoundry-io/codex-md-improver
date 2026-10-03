"""Per-directory physical totals, conditions and incomplete-frontier evidence."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
from references import summarize_reading_paths


class DirectoryContracts(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build

    def summary(self, graph, path, scenario=None):
        summaries = summarize_reading_paths(graph)
        rows = (summaries.get('directory_summaries_by_scenario', {}).get(scenario, {})
                if scenario else summaries.get('directory_summaries', {}))
        row = rows.get(str(path))
        self.assertIsInstance(row, dict, 'Required per-directory summary is missing')
        return row

    def test_directory_file_count_conditions_and_empty_control(self):
        docs, empty = self.root / 'docs', self.root / 'empty'
        empty.mkdir()
        for index in range(200):
            self.put(docs / f'{index}.md', 'x' * 5120)
        self.put(self.source, 'Read [docs](docs/) before editing.\nRead [empty](empty/).\n')
        graph = self.build()
        for scenario in (None, 'one'):
            with self.subTest(scenario=scenario):
                row = self.summary(graph, docs, scenario)
                self.assertEqual(row['physical_text_files'], 200)
                self.assertEqual(row['unique_text_bytes'], 1024000)
                self.assertEqual(row['frontier_counts'], {})
                self.assertFalse(row['lower_bound'])
                self.assertTrue(any(c['source'] == str(self.source) and c['target_path'] == str(docs)
                                    and c['occurrence_id'] and c['scenario_id'] == 'one'
                                    and 'before editing' in c['condition'] for c in row['read_conditions']))
                zero = self.summary(graph, empty, scenario)
                self.assertEqual((zero['physical_text_files'], zero['unique_text_bytes']), (0, 0))
                self.assertFalse(zero['lower_bound'])

    def test_aliases_and_scenario_union_preserve_physical_counts(self):
        shared = self.base / 'shared'
        guide = self.put(shared / 'guide.md', 'Read `leaf.md`.\n')
        os.link(guide, shared / 'alias.md')
        a = self.put(self.root / 'a/leaf.md', 'A')
        b = self.put(self.root / 'b/leaf.md', 'B' * 20)
        self.put(self.source, 'Read [shared](' + str(shared) + ').\n')
        chains = [self.chain(a.parent, scenario='a'), self.chain(b.parent, scenario='b')]
        bases = {str(p): {'kind': 'scenario_cwd'} for p in (guide, shared / 'alias.md')}
        graph = self.build(chains, bases)
        for scenario, leaf in (('a', a), ('b', b)):
            with self.subTest(scenario=scenario):
                row = self.summary(graph, shared, scenario)
                self.assertEqual(row['physical_text_files'], 2)
                self.assertEqual(row['unique_text_bytes'], guide.stat().st_size + leaf.stat().st_size)
                self.assertEqual({c['source'] for c in row['read_conditions'] if c['target_path'] == str(leaf)},
                                 {str(guide), str(shared / 'alias.md')})
        aggregate = self.summary(graph, shared)
        self.assertEqual(aggregate['physical_text_files'], 3)
        self.assertEqual(aggregate['unique_text_bytes'], guide.stat().st_size + 21)
        self.assertEqual({c['scenario_id'] for c in aggregate['read_conditions']}, {'a', 'b'})

    def test_frontier_kinds_and_conditions_do_not_count_cycles_or_urls(self):
        docs = self.root / 'docs'
        guide = self.put(docs / 'guide.md', 'Read [missing](missing.md).\nmaybe.md\n'
                         'Read [self](guide.md).\nRead [web](https://example.org).\n')
        self.put(docs / 'binary.bin', b'\0binary')
        self.put(docs / 'skill/SKILL.md', 'excluded instruction')
        self.put(docs / 'denied/hidden.md', 'hidden')
        self.put(self.source, 'Read [docs](docs/).\n')
        original = Path.iterdir
        def iterdir(path):
            if path == docs / 'denied':
                raise PermissionError('synthetic directory denial')
            return original(path)
        with patch.object(Path, 'iterdir', iterdir):
            graph = self.build()
        row = self.summary(graph, docs, 'one')
        self.assertEqual(row['physical_text_files'], 1)
        self.assertEqual(row['unique_text_bytes'], guide.stat().st_size)
        self.assertEqual(row['frontier_counts'], {'missing_target': 1, 'unresolved': 1,
                         'binary': 1, 'excluded_skill': 1, 'blocked_frontier': 1})
        self.assertTrue(row['lower_bound'])
        self.assertTrue(any(c['source'] == str(guide) and c['condition'] == 'maybe.md'
                            for c in row['read_conditions']))
        denied = self.summary(graph, docs / 'denied', 'one')
        self.assertEqual(denied['physical_text_files'], 0)
        self.assertEqual(denied['frontier_counts'], {'blocked_frontier': 1})
        self.assertTrue(denied['lower_bound'])
