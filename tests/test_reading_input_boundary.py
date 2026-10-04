"""Persisted reading structures must reject at the CLI input boundary."""
import copy
import hashlib
import json
import unittest

import test_reporting as fixtures
import test_reporting_edges as edge_fixtures


class ReadingInputBoundary(unittest.TestCase):
    setUp = fixtures.ReportingTests.setUp
    make_audit = fixtures.ReportingTests.make_audit
    evidence = fixtures.ReportingTests.evidence
    assessment = fixtures.ReportingTests.assessment
    cli = edge_fixtures.ReportingEdges.cli

    def run_report(self, audit, name):
        raw = json.dumps(audit, ensure_ascii=False).encode('utf-8')
        scan = self.root / (name + '-scan.json')
        scan.write_bytes(raw)
        assessment = self.assessment(audit=audit)
        assessment['audit_sha256'] = hashlib.sha256(raw).hexdigest()
        judgment = self.root / (name + '-assessment.json')
        judgment.write_text(json.dumps(assessment), encoding='utf-8')
        out = self.root / (name + '-out')
        result = self.cli('report', '--audit', scan, '--assessment', judgment, '--out', out)
        self.assertEqual(scan.read_bytes(), raw)
        return result, out

    def reject(self, variants):
        for index, (part, values) in enumerate(variants):
            with self.subTest(part=part, values=values):
                audit = copy.deepcopy(self.audit)
                audit[part].update(values)
                result, out = self.run_report(audit, str(index))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse(out.exists(), 'Malformed input must fail before output creation')

    def test_malformed_occurrence_and_directory_containers(self):
        self.reject([
            ('graph', {'occurrences': [0]}),
            ('graph', {'occurrences': {}}),
            ('graph', {'occurrences': None}),
            ('reading_summary', {'directory_summaries_by_scenario': []}),
            ('reading_summary', {'directory_summaries_by_scenario': None}),
            ('reading_summary', {'directory_summaries_by_scenario': {'s': []}}),
            ('reading_summary', {'directory_summaries_by_scenario': {'s': {'/docs': 0}}}),
        ])

    def test_new_reading_metrics_are_nonnegative_integers_or_unknown(self):
        variants = []
        for bad in (-1, True, '7', 2.5, []):
            variants.append(('reading_summary', {'physical_text_files': bad}))
            for name in ('unique_text_bytes', 'physical_text_files'):
                variants.append(('reading_summary', {'directory_summaries_by_scenario':
                                                    {'s': {'/docs': {name: bad}}}}))
        self.reject(variants)

    def test_occurrence_identity_alternatives_and_state_kind_are_typed(self):
        variants = []
        for name in ('scenario_id', 'cwd', 'source', 'target_text', 'classification', 'condition', 'status'):
            variants.append(('graph', {'occurrences': [{'status': 'unresolved', name: []}]}))
        variants.extend([
            ('graph', {'occurrences': [{'status': 'unresolved', 'alternatives': '/docs'}]}),
            ('graph', {'occurrences': [{'status': 'unresolved', 'alternatives': [0]}]}),
            ('graph', {'states': {'s': {'kind': []}}}),
        ])
        self.reject(variants)

    def test_reading_completeness_and_loader_metrics_reject_wrong_types(self):
        cases = []
        for part in ('graph', 'reading_summary'):
            for name in ('partial', 'text_read_complete'):
                audit = copy.deepcopy(self.audit)
                audit[part][name] = 'false'
                cases.append(audit)
        for name, value in (('partial', 'false'), ('scenario_id', []), ('cwd', []), ('environment_group_id', []),
                            ('project_original_bytes', -1), ('project_included_bytes', True)):
            for grouped in (False, True):
                audit = copy.deepcopy(self.audit)
                member = {'scenario_id': 's', 'cwd': str(self.project), name: value}
                audit['groups' if grouped else 'chains'] = [{'members': [member]}] if grouped else [member]
                cases.append(audit)
        audit = copy.deepcopy(self.audit)
        audit['inventory_complete'] = 'false'
        cases.append(audit)
        audit = copy.deepcopy(self.audit)
        audit['reading_summary']['directory_summaries_by_scenario'] = {'s': {'/docs': {'lower_bound': 'false'}}}
        cases.append(audit)
        for global_source in (None, [], {'original_bytes': -1}, {'included_bytes': '7'}):
            audit = copy.deepcopy(self.audit)
            audit['chains'] = [{'global_source': global_source}]
            cases.append(audit)
        for index, audit in enumerate(cases):
            with self.subTest(index=index):
                result, out = self.run_report(audit, str(index))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse(out.exists())

    def test_sparse_and_explicit_unknown_valid_inputs_still_render(self):
        for index, detailed in enumerate((False, True)):
            with self.subTest(detailed=detailed):
                audit = copy.deepcopy(self.audit)
                if detailed:
                    audit['chains'] = [{'scenario_id': 's', 'cwd': str(self.project),
                                        'environment_group_id': '', 'global_source': {},
                                        'project_original_bytes': 0, 'project_included_bytes': None}]
                    audit['graph']['occurrences'] = [{'status': 'resolved', 'condition': None,
                        'source': '', 'target_text': '', 'classification': '', 'scenario_id': None,
                        'cwd': None, 'alternatives': []}]
                    audit['reading_summary'].update(physical_text_files=None,
                        directory_summaries_by_scenario={'s': {'/docs': {
                            'unique_text_bytes': None, 'physical_text_files': 0, 'lower_bound': True}}})
                result, out = self.run_report(audit, str(index))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(json.loads((out / 'manifest.json').read_text())['phase'], 'finished')
                self.assertIn('Known unique reachable text bytes', (out / 'audit.md').read_text())


if __name__ == '__main__':
    unittest.main()
