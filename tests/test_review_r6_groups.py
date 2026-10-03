"""Ordered shared-budget warnings retain raw-volume and gate distinctions."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_discovery as fixtures
from discovery import scan
from reporting import compare_reports, render_audit


class GroupBudget(unittest.TestCase):
    setUp = fixtures.DiscoveryTests.setUp
    put = fixtures.DiscoveryTests.put
    request = fixtures.DiscoveryTests.request
    cli = fixtures.DiscoveryTests.cli

    def setup_group(self, sizes, limit=32768, trust='trusted'):
        (self.root / 'AGENTS.md').unlink(missing_ok=True)
        cwds = []
        for index, size in enumerate(sizes):
            cwd = self.root / str(index)
            self.put(cwd / 'AGENTS.md', 'x' * size)
            cwds.append(str(cwd))
        return {'non_project': {'limit': 32768, 'fallback_names': [], 'root_markers': []},
                'trust': {str(self.root): 'trusted', **{cwd: 'trusted' for cwd in cwds}},
                'environment_groups': [{'id': 'pair', 'cwds': cwds,
                    'effective_loader_settings': {'limit': limit, 'fallback_names': [], 'root_markers': [], 'trust': trust}}]}

    def test_combined_overflow_signals_scan_render_and_comparison(self):
        settings = self.setup_group([18000, 18000])
        proc, report = self.cli(settings)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        group = report['groups'][0]
        self.assertEqual(group.get('project_original_bytes'), 36000)
        self.assertTrue(group.get('warning'))
        self.assertTrue(group.get('raw_volume_exceeds_budget'))
        self.assertEqual([m['project_included_bytes'] for m in group['members']], [18000, 14768])
        self.assertFalse(any(m['warning'] or m['raw_volume_exceeds_budget'] for m in group['members']))
        self.assertIn('group pair', render_audit(report))
        delta = compare_reports(report, report)
        self.assertEqual(delta['exit_code'], 1)
        self.assertGreaterEqual(delta['remaining_scan_findings'].get('loader_warning_count', 0), 1)

    def test_exact_warning_and_overflow_boundaries(self):
        for total, warning, excess in [(29491, False, False), (29492, True, False),
                                       (32768, True, False), (32769, True, True)]:
            with self.subTest(total=total):
                settings = self.setup_group([total // 2, total - total // 2])
                group = scan(self.request(settings))['groups'][0]
                self.assertEqual(group.get('project_original_bytes'), total)
                self.assertIs(group.get('warning'), warning)
                self.assertIs(group.get('raw_volume_exceeds_budget'), excess)

    def test_exhausted_member_is_distinct_from_gate(self):
        settings = self.setup_group([32768, 1])
        member = scan(self.request(settings))['groups'][0]['members'][1]
        self.assertEqual(member['loader_outcome'], 'budget_exhausted')
        self.assertEqual(member['sources'][0]['omission'], 'budget_exhausted')
        self.assertEqual(member['project_included_bytes'], 0)
        self.assertEqual(member['project_retained_raw_bytes'], 0)
        self.assertIsNone(member['modeled_loader_error'])

    def test_zero_and_untrusted_gates_remain_distinct_controls(self):
        for limit, trust in [(0, 'trusted'), (32768, 'untrusted')]:
            with self.subTest(limit=limit, trust=trust):
                settings = self.setup_group([2, 2], limit, trust)
                for member in scan(self.request(settings))['groups'][0]['members']:
                    self.assertEqual(member['loader_outcome'], 'omitted_by_gate')
                    self.assertEqual(member['project_included_bytes'], 0)

    def test_unknown_original_volume_is_not_replaced_by_inclusion(self):
        settings = self.setup_group([10, 10])
        blocked = self.root / '1/AGENTS.md'
        original = Path.stat
        def stat(path, *args, **kwargs):
            if path == blocked:
                raise PermissionError('synthetic inaccessible selected metadata')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'stat', stat):
            report = scan(self.request(settings))
        group = report['groups'][0]
        self.assertIsNone(group.get('project_original_bytes'))
        self.assertIsNone(group.get('warning'))
        self.assertIsNone(group.get('raw_volume_exceeds_budget'))
        self.assertEqual(report['exit_code'], 3)

    def test_unknown_limit_empty_volume_and_independent_controls(self):
        settings = self.setup_group([10, 10], None)
        group = scan(self.request(settings))['groups'][0]
        self.assertIsNone(group.get('warning'))
        self.assertIsNone(group.get('raw_volume_exceeds_budget'))
        settings = self.setup_group([0, 0])
        group = scan(self.request(settings))['groups'][0]
        self.assertEqual(group.get('project_original_bytes'), 0)
        self.assertIs(group.get('warning'), False)
        settings = self.setup_group([18000, 18000])
        settings['environment_groups'] = []
        report = scan(self.request(settings))
        self.assertEqual(report['exit_code'], 0)

    def test_shared_prefix_is_counted_per_environment(self):
        settings = self.setup_group([0, 0], 20)
        for i in range(2):
            (self.root / str(i) / 'AGENTS.md').unlink()
        self.put(self.root / 'AGENTS.md', 'x' * 9)
        settings['environment_groups'][0]['effective_loader_settings']['root_markers'] = ['.git']
        group = scan(self.request(settings))['groups'][0]
        self.assertEqual([m['project_original_bytes'] for m in group['members']], [9, 9])
        self.assertEqual(group.get('project_original_bytes'), 18)
        self.assertEqual(group['project_included_bytes'], 18)
        self.assertTrue(group.get('warning'))
