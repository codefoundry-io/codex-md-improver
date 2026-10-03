"""Native case aliases retain output opt-in and owned-output boundaries."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_review_r5_output as fixtures


class NativeOutputBoundaries(unittest.TestCase):
    setUp = fixtures.OutputContracts.setUp
    make_audit = fixtures.OutputContracts.make_audit
    evidence = fixtures.OutputContracts.evidence
    assessment = fixtures.OutputContracts.assessment
    finding = fixtures.OutputContracts.finding
    inputs = fixtures.OutputContracts.inputs
    cli = fixtures.OutputContracts.cli

    def alias(self, path):
        alias = path.with_name(path.name.upper())
        if alias == path or not alias.exists():
            self.skipTest('fixture volume is case-sensitive; native alias unavailable')
        self.assertTrue(alias.samefile(path))
        return alias

    def check_precreation(self, command, linked=False):
        target = self.project
        if linked:
            target = self.root / 'linked'
            target.mkdir()
            self.audit['graph']['states']['linked-directory'] = {'path': str(target), 'kind': 'directory'}
        out = self.alias(target) / 'audit-out'
        args = self.inputs()[command]
        before = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in target.rglob('*') if p.is_file()}
        result = self.cli(command, *args, '--out', out)
        with self.subTest(check='refuse before creation'):
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        with self.subTest(check='no output or receipt'):
            self.assertFalse(out.exists())
        with self.subTest(check='input tree unchanged'):
            after = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in target.rglob('*') if p.is_file()}
            self.assertEqual(after, before)

    def test_native_scan_project_case_alias_is_refused_before_output(self):
        self.check_precreation('scan')

    def test_native_report_project_case_alias_is_refused_before_output(self):
        self.check_precreation('report')

    def test_native_compare_project_case_alias_is_refused_before_output(self):
        self.check_precreation('compare')

    def test_native_report_recorded_directory_alias_is_refused_before_output(self):
        self.check_precreation('report', linked=True)

    def test_native_compare_recorded_directory_alias_is_refused_before_output(self):
        self.check_precreation('compare', linked=True)

    def test_native_opted_in_scan_excludes_owned_cwd(self):
        out = self.alias(self.project) / 'audit-out'
        result = self.cli('scan', *self.inputs()['scan'], '--out', out, '--allow-output-in-target')
        self.assertIn(result.returncode, (0, 1), result.stderr)
        audit = json.loads((out / 'audit.json').read_text())
        self.assertFalse(any(Path(c['cwd']).samefile(out) for c in audit['chains']))
        self.assertTrue(any(f['kind'] == 'owned_output' and Path(f['path']).samefile(out)
                            for f in audit['frontiers']))
        self.assertTrue(json.loads((out / 'manifest.json').read_text())['allow_output_in_target'])

    def test_native_report_and_compare_explicit_opt_in_controls(self):
        alias = self.alias(self.project)
        inputs = self.inputs()
        for command in ('report', 'compare'):
            with self.subTest(command=command):
                out = alias / ('allowed-' + command)
                result = self.cli(command, *inputs[command], '--out', out, '--allow-output-in-target')
                self.assertIn(result.returncode, (0, 1), result.stderr)
                manifest = json.loads((out / 'manifest.json').read_text())
                self.assertTrue(manifest['complete'])
                self.assertTrue(manifest['allow_output_in_target'])

    def test_outside_parent_control(self):
        inputs = self.inputs()
        for command, args in inputs.items():
            with self.subTest(command=command):
                out = self.root / ('outside-' + command)
                result = self.cli(command, *args, '--out', out)
                self.assertIn(result.returncode, (0, 1), result.stderr)
                self.assertTrue(json.loads((out / 'manifest.json').read_text())['complete'])

    def test_compare_missing_recorded_project_remains_a_snapshot_control(self):
        args = self.inputs()['compare']
        self.source.unlink()
        self.project.rmdir()
        out = self.root / 'snapshot-comparison'
        result = self.cli('compare', *args, '--out', out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads((out / 'manifest.json').read_text())['complete'])

    def test_distinct_case_sensitive_sibling_remains_outside_control(self):
        sibling = self.project.with_name(self.project.name.upper())
        if sibling.exists():
            self.skipTest('native case-sensitive sibling fixture requires distinct names')
        sibling.mkdir()
        self.assertFalse(sibling.samefile(self.project))
        out = sibling / 'allowed'
        result = self.cli('scan', *self.inputs()['scan'], '--out', out)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertTrue(json.loads((out / 'manifest.json').read_text())['complete'])

    def test_native_linked_directory_alias_requires_late_refusal(self):
        linked = self.root / 'shared'
        linked.mkdir()
        alias = self.alias(linked)
        (linked / 'prior.md').write_text('Prior ordinary report.')
        self.source.write_text(self.source.read_text() + 'Read [shared](' + str(alias) + '/).\n')
        self.audit = self.make_audit()
        out = linked / 'audit-out'
        result = self.cli('scan', *self.inputs()['scan'], '--out', out)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        manifest = json.loads((out / 'manifest.json').read_text())
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['phase'], 'error')

    def test_native_linked_directory_opt_in_preserves_prior_input_control(self):
        linked = self.root / 'shared'
        linked.mkdir()
        alias = self.alias(linked)
        prior = linked / 'prior.md'
        prior.write_text('Prior ordinary report.')
        self.source.write_text(self.source.read_text() + 'Read [shared](' + str(alias) + '/).\n')
        self.audit = self.make_audit()
        out = linked / 'audit-out'
        result = self.cli('scan', *self.inputs()['scan'], '--out', out, '--allow-output-in-target')
        self.assertIn(result.returncode, (0, 1), result.stderr)
        audit = json.loads((out / 'audit.json').read_text())
        aliases = [Path(p) for n in audit['graph']['nodes'].values() for p in n['aliases']]
        self.assertTrue(any(p.samefile(prior) for p in aliases))
        self.assertFalse(any(p.parent.samefile(out) for p in aliases))
        self.assertTrue(any(b['kind'] == 'owned_output' and Path(b['path']).samefile(out)
                            for b in audit['graph']['boundaries']))

    def test_native_direct_owned_file_remains_refused_with_opt_in_control(self):
        parent = self.root / 'results'
        parent.mkdir()
        alias = self.alias(parent)
        self.source.write_text(self.source.read_text() + 'Read [receipt](' + str(alias / 'audit-out/manifest.json') + ').\n')
        self.audit = self.make_audit()
        out = parent / 'audit-out'
        result = self.cli('scan', *self.inputs()['scan'], '--out', out, '--allow-output-in-target')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(json.loads((out / 'manifest.json').read_text())['complete'])
