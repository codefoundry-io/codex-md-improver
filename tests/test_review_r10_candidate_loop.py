"""Completed candidate retargets to loops remain branch-local failures."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
import discovery
import md_improver


class CandidateLoop(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def check_loop(self, force_runtime_error):
        self.put(self.source, 'Read [docs](docs/).\n')
        guide = self.put(self.root / 'docs/guide.md', 'Read [old](../old.md).\n')
        good = self.put(self.root / 'docs/good.md', 'Sure! Healthy sibling.')
        self.put(self.root / 'old.md', 'Former child.')
        records, canonical = md_improver._candidate_records, discovery.canonical
        def retarget(graph, scenarios, content, selected):
            guide.unlink()
            guide.symlink_to('guide.md')
            def platform_result(path):
                if force_runtime_error and path == guide:
                    raise RuntimeError('Symlink loop from Path.resolve on Python3.11/3.12')
                return canonical(path)
            with patch.object(discovery, 'canonical', platform_result):
                return records(graph, scenarios, content, selected)
        out = self.base / 'out'
        with patch.object(md_improver, '_candidate_records', retarget):
            code = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                                    '--codex-home', str(self.home), '--out', str(out)])
        self.assertEqual(code, 3)
        audit = json.loads((out / 'audit.json').read_text())
        self.assertTrue(audit['partial'])
        self.assertTrue(any(c['path'] == str(good) for c in audit['candidates']))
        rows = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
        self.assertTrue(any(r['terminal_path'] == str(guide) and r['terminal_kind'] == 'blocked_frontier'
                            and r['lower_bound'] for r in rows))
        self.assertFalse(any(r['terminal_path'].endswith('/old.md') for r in rows))

    def test_runtime_error_observation_is_branch_local(self): self.check_loop(True)
    def test_native_completed_symlink_loop_is_branch_local(self): self.check_loop(False)
