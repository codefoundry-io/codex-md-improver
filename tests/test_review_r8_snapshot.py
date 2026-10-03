"""Candidate observations must match the graph's source snapshot."""
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
import md_improver


class CandidateSnapshot(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def run_case(self, replacement):
        self.put(self.source, 'Read [docs](docs/).\n')
        original = b'Read [old](../old.md).\n'
        changing = self.put(self.root / 'docs/changing.md', original)
        good = self.put(self.root / 'docs/good.md', 'Sure! Follow the guide.\n')
        old = self.put(self.root / 'old.md', 'Original nested evidence.')
        new = self.put(self.root / 'new.md', 'New dependency.')
        before = changing.stat()
        candidate_records = md_improver._candidate_records
        def replace_then_extract(graph, scenarios, content, selected):
            if replacement is not None:
                staged = self.put(self.base / 'replacement.md', replacement)
                staged.replace(changing)
                self.assertNotEqual((before.st_dev, before.st_ino),
                                    (changing.stat().st_dev, changing.stat().st_ino))
            return candidate_records(graph, scenarios, content, selected)
        out = self.base / 'out'
        with patch.object(md_improver, '_candidate_records', replace_then_extract):
            code = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                                    '--codex-home', str(self.home), '--out', str(out)])
        report = json.loads((out / 'audit.json').read_text())
        rows = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
        return code, report, rows, changing, good, old, new, original

    def test_replaced_bytes_are_partial_without_misbound_candidates(self):
        code, report, rows, changing, good, old, new, original = self.run_case(b'Sure! Read [new](../new.md).\n')
        self.assertEqual(code, 3)
        self.assertTrue(report['partial'])
        self.assertFalse(report['text_read_complete'])
        self.assertFalse(any(c['path'] == str(changing) for c in report['candidates']))
        self.assertTrue(any(c['path'] == str(good) for c in report['candidates']))
        self.assertTrue(any(r['terminal_path'] == str(changing) and r['terminal_kind'] == 'changed_during_read'
                            and r['lower_bound'] for r in rows))
        self.assertFalse(any(Path(r['terminal_path']).resolve() in (old, new) for r in rows))
        node = next(n for n in report['graph']['nodes'].values() if str(changing) in n['aliases'])
        self.assertEqual(node['sha256'], hashlib.sha256(original).hexdigest())
        scenario = report['chains'][0]['scenario_id']
        for container in (report['graph'], report['reading_summary']):
            for row in (container['directory_summaries'][str(changing.parent)],
                        container['directory_summaries_by_scenario'][scenario][str(changing.parent)]):
                self.assertEqual(row['frontier_counts'], {'changed_during_read': 1})
                self.assertTrue(row['lower_bound'])
                self.assertEqual(row['unique_text_bytes'], len(original) + good.stat().st_size)
                self.assertFalse(any(c['source'] == str(changing) for c in row['read_conditions']))

    def test_identical_bytes_on_new_inode_remain_valid(self):
        self.check_healthy(b'Read [old](../old.md).\n')

    def test_unchanged_source_control(self):
        self.check_healthy(None)

    def check_healthy(self, replacement):
        code, report, rows, changing, good, old, new, original = self.run_case(replacement)
        self.assertIn(code, (0, 1))
        self.assertFalse(report['partial'])
        self.assertTrue(report['text_read_complete'])
        self.assertEqual({Path(r['terminal_path']).resolve() for r in rows}, {old, good})
        self.assertFalse(any(r['lower_bound'] for r in rows))
        for candidate in report['candidates']:
            self.assertEqual(candidate['source_sha256'], hashlib.sha256(Path(candidate['path']).read_bytes()).hexdigest())
