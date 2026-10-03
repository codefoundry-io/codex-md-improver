"""New output ownership and Python 3.11/3.12 path-loop error contracts."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_reporting as fixtures
import test_reporting_edges as edge_fixtures
from reporting import enrich_audit


class OutputContracts(unittest.TestCase):
    setUp = fixtures.ReportingTests.setUp
    make_audit = fixtures.ReportingTests.make_audit
    evidence = fixtures.ReportingTests.evidence
    assessment = fixtures.ReportingTests.assessment
    finding = fixtures.ReportingTests.finding
    cli = edge_fixtures.ReportingEdges.cli

    def inputs(self):
        (self.root / 'home').mkdir(exist_ok=True)
        raw = json.dumps(self.audit).encode()
        audit_path = self.root / 'input-audit.json'
        audit_path.write_bytes(raw)
        assessment = self.assessment()
        assessment['audit_sha256'] = hashlib.sha256(raw).hexdigest()
        assessment_path = self.root / 'input-assessment.json'
        assessment_path.write_text(json.dumps(assessment))
        report = enrich_audit(self.audit, self.assessment())
        report_path = self.root / 'input-report.json'
        report_path.write_text(json.dumps(report))
        return {'scan': ['--project', str(self.project), '--codex-home', str(self.root / 'home')],
                'report': ['--audit', str(audit_path), '--assessment', str(assessment_path)],
                'compare': ['--before', str(report_path), '--after', str(report_path)]}

    def test_missing_output_parents_are_never_created(self):
        for command, args in self.inputs().items():
            with self.subTest(command=command):
                parent = self.root / ('missing-' + command)
                result = self.cli(command, *args, '--out', parent / 'run')
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(parent.exists())

    def test_opted_in_scan_does_not_create_new_inventory_parent(self):
        args = self.inputs()['scan']
        parent = self.project / 'new-parent'
        result = self.cli('scan', *args, '--allow-output-in-target', '--out', parent / 'run')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(parent.exists())

    def test_existing_parent_controls(self):
        for command, args in self.inputs().items():
            with self.subTest(command=command):
                parent = self.root / ('existing-' + command)
                parent.mkdir()
                out = parent / 'run'
                result = self.cli(command, *args, '--out', out)
                self.assertIn(result.returncode, (0, 1), result.stderr)
                self.assertTrue(json.loads((out / 'manifest.json').read_text())['complete'])

    def test_sensitive_path_loop_returns_error_receipt_for_scan_and_report(self):
        inputs = self.inputs()
        home = self.root / 'home'
        home.mkdir(exist_ok=True)
        (home / 'auth.json').symlink_to('auth.json')
        for command in ('scan', 'report'):
            with self.subTest(command=command):
                out = self.root / ('loop-' + command)
                result = self.cli(command, *inputs[command], '--out', out)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                manifest = json.loads((out / 'manifest.json').read_text())
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['phase'], 'error')
                if command == 'scan':
                    self.assertEqual(json.loads((out / 'audit.json').read_text())['exit_code'], 2)

    def test_looping_output_parent_returns_error_before_output(self):
        inputs = self.inputs()
        loop = self.root / 'loop'
        loop.symlink_to('loop')
        for command, args in inputs.items():
            with self.subTest(command=command):
                result = self.cli(command, *args, '--out', loop / command)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_looping_source_is_unverifiable_evidence(self):
        assessment = self.assessment(findings=[self.finding()])
        self.source.unlink()
        self.source.symlink_to(self.source.name)
        try:
            with self.assertRaisesRegex(ValueError, 'Source evidence cannot be verified'):
                enrich_audit(self.audit, assessment)
        except RuntimeError as error:
            self.fail('Path-loop error escaped source verification: ' + str(error))
