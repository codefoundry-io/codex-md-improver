"""Persisted frontier corruption is an input error, never exit-1 success."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_reporting as fixtures
from reporting import enrich_audit, report_hash


class PersistedFrontiers(unittest.TestCase):
    setUp = fixtures.ReportingTests.setUp
    make_audit = fixtures.ReportingTests.make_audit

    def run_report(self, frontiers):
        self.audit['frontiers'] = frontiers
        audit = self.root / 'audit.json'
        audit.write_text(json.dumps(self.audit))
        assessment = self.root / 'assessment.json'
        assessment.write_text(json.dumps({'schema_version': 1,
            'audit_sha256': hashlib.sha256(audit.read_bytes()).hexdigest()}))
        out = self.root / ('out-' + str(len(list(self.root.glob('out-*')))))
        result = subprocess.run([sys.executable, str(PROJECT / 'skills/codex-md-improver/scripts/md_improver.py'),
            'report', '--audit', str(audit), '--assessment', str(assessment), '--out', str(out)],
            capture_output=True, text=True, timeout=10)
        return result, out

    def test_invalid_frontier_shapes_reject_without_traceback(self):
        for invalid in (['x'], {'k': 1}, None, [None], [{}], [{'kind': 3, 'path': '/tmp/x'}],
                        [{'kind': 'git_administration', 'path': 7}],
                        [{'kind': 'git_administration', 'path': 'relative'}]):
            with self.subTest(invalid=invalid):
                result, out = self.run_report(invalid)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                if out.exists():
                    manifest = json.loads((out / 'manifest.json').read_text())
                    self.assertEqual(manifest['phase'], 'error')
                    self.assertFalse(manifest['complete'])

    def test_empty_and_valid_frontier_controls(self):
        for frontiers in ([], [{'kind': 'git_administration', 'path': str(self.root / 'store')}],
                          [{'kind': 'blocked', 'path': str(self.root / 'blocked'), 'error': 'PermissionError'}]):
            with self.subTest(frontiers=frontiers):
                result, _ = self.run_report(frontiers)
                self.assertNotEqual(result.returncode, 2, result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_direct_report_api_rejects_malformed_frontiers(self):
        self.audit['frontiers'] = ['x']
        with self.assertRaises(ValueError):
            enrich_audit(self.audit, {'schema_version': 1, 'audit_sha256': report_hash(self.audit)})

    def test_compare_rejects_malformed_frontiers_before_output(self):
        self.audit['frontiers'] = ['x']
        path = self.root / 'audit.json'
        path.write_text(json.dumps(self.audit))
        out = self.root / 'compare'
        result = subprocess.run([sys.executable, str(PROJECT / 'skills/codex-md-improver/scripts/md_improver.py'),
            'compare', '--before', str(path), '--after', str(path), '--out', str(out)],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(out.exists())
