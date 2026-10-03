"""Portable surrogate-output regressions and a native Linux filename fixture."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures
import test_reporting as report_fixtures
import test_reporting_edges as edge_fixtures
import discovery
import md_improver
from reporting import report_hash

BAD = '/synthetic/name-' + chr(0xDCFF)


class OutputEncoding(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def test_json_paths_keys_errors_roundtrip(self):
        value = {'path': BAD, BAD: {'error': BAD, 'unicode': '한글😀'}}
        path = self.base / 'receipt.json'
        try:
            md_improver._write_json(path, value)
        except UnicodeError as error:
            self.fail('JSON encoding escaped receipt boundary: ' + type(error).__name__)
        self.assertEqual(json.loads(path.read_text(encoding='utf-8')), value)
        self.assertIn('한글😀', path.read_text(encoding='utf-8'))

    def test_report_hash_handles_surrogates_without_changing_unicode_control(self):
        for value in ({'path': BAD}, {'unicode': '한글😀'}):
            with self.subTest(value=ascii(value)):
                expected = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                    separators=(',', ':')).encode('utf-8', errors='backslashreplace')).hexdigest()
                try:
                    actual = report_hash(value)
                except UnicodeError as error:
                    self.fail('Canonical hash rejected surrogate: ' + type(error).__name__)
                self.assertEqual(actual, expected)

    def test_error_and_interrupt_receipts_escape_surrogates(self):
        original_scan = discovery.scan
        def scan(*args, **kwargs):
            result = original_scan(*args, **kwargs)
            result['diagnostic_path'] = BAD
            return result
        for index, (failure, expected, phase) in enumerate([
                (ValueError('bad path ' + BAD), 2, 'error'),
                (md_improver.ScanInterrupted('synthetic signal'), 3, 'interrupted')]):
            with self.subTest(phase=phase):
                out = self.base / ('failed-' + str(index))
                sink = io.BytesIO()
                stderr = io.TextIOWrapper(sink, encoding='utf-8', errors='strict')
                with patch.object(discovery, 'scan', scan), patch('references.build_reference_graph', side_effect=failure), patch.object(sys, 'stderr', stderr):
                    try:
                        code = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                            '--codex-home', str(self.home), '--out', str(out)])
                    except UnicodeError as error:
                        self.fail('Receipt or diagnostic re-raised: ' + type(error).__name__)
                stderr.flush()
                self.assertEqual(code, expected)
                audit = json.loads((out / 'audit.json').read_text(encoding='utf-8'))
                manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
                self.assertEqual(audit['diagnostic_path'], BAD)
                self.assertEqual(audit['exit_code'], expected)
                self.assertEqual(manifest['phase'], phase)
                self.assertFalse(manifest['complete'])
                self.assertNotIn('Traceback', sink.getvalue().decode('utf-8'))
                stderr.detach()

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Native Linux bytes-name fixture')
    def test_linux_non_utf8_names_keep_complete_receipts_and_routes(self):
        raw_dir = os.fsencode(self.root) + b'/docs-\xff'
        os.mkdir(raw_dir)
        raw_file = raw_dir + b'/guide-\xfe.md'
        with open(raw_file, 'wb') as stream:
            stream.write(b'Sure! Follow the guide.\n')
        self.put(self.source, 'Read [project](./) before editing.\n')
        out = self.base / 'linux-run'
        result = subprocess.run([sys.executable, str(fixtures.SOT / 'scripts/md_improver.py'), 'scan',
            '--project', str(self.root), '--codex-home', str(self.home), '--out', str(out)],
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8:strict'}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        audit = json.loads((out / 'audit.json').read_text(encoding='utf-8'))
        self.assertFalse(audit['partial'])
        self.assertTrue(json.loads((out / 'manifest.json').read_text())['complete'])
        routes = [json.loads(s) for s in (out / 'routes.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertTrue(any(r['terminal_path'] and os.fsencode(r['terminal_path']) == raw_file for r in routes))
        self.assertTrue(any(os.fsencode(a) == raw_file for n in audit['graph']['nodes'].values() for a in n['aliases']))
        self.assertIn('\\udcfe', (out / 'audit.md').read_text(encoding='utf-8'))


class ReportEncoding(unittest.TestCase):
    setUp = report_fixtures.ReportingTests.setUp
    make_audit = report_fixtures.ReportingTests.make_audit
    evidence = report_fixtures.ReportingTests.evidence
    assessment = report_fixtures.ReportingTests.assessment
    cli = edge_fixtures.ReportingEdges.cli

    def test_report_and_compare_outputs_preserve_surrogate_json(self):
        audit_path = self.root / 'input.json'
        audit_path.write_text(json.dumps(self.audit))
        proposal = {'id': 'move', 'kind': 'replacement', 'evidence': [self.evidence()],
            'destination': BAD, 'replacement': '한글😀', 'reason': 'surrogate destination',
            'affected_references': [str(self.source)], 'expected_byte_delta': 0,
            'expected_reading_change': 'unchanged', 'required_decisions': []}
        assessment = self.assessment(proposals=[proposal])
        assessment['audit_sha256'] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
        assessment_path = self.root / 'assessment.json'
        assessment_path.write_text(json.dumps(assessment))
        out = self.root / 'report'
        proc = self.cli('report', '--audit', audit_path, '--assessment', assessment_path, '--out', out)
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        saved = json.loads((out / 'audit.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['proposals'][0]['destination'], BAD)
        text = (out / 'audit.md').read_text(encoding='utf-8')
        self.assertIn('\\udcff', text)
        self.assertIn('한글😀', text)
        delta = self.root / 'compare'
        proc = self.cli('compare', '--before', out / 'audit.json', '--after', out / 'audit.json', '--out', delta)
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        self.assertTrue(json.loads((delta / 'manifest.json').read_text())['complete'])
        (delta / 'delta.md').read_text(encoding='utf-8')
