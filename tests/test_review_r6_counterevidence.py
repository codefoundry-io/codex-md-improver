"""Existing proposal validation and orthogonal owner-status evidence."""
import copy
from pathlib import Path
import sys
import unittest

PROJECT = Path('/Users/chaniri/codex_workspace/workspace/codex-md-improver')
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_reporting as fixtures
from reporting import enrich_audit, compare_reports


class ReviewCounterevidence(unittest.TestCase):
    setUp = fixtures.ReportingTests.setUp
    make_audit = fixtures.ReportingTests.make_audit
    evidence = fixtures.ReportingTests.evidence
    assessment = fixtures.ReportingTests.assessment
    finding = fixtures.ReportingTests.finding

    def test_addition_observation_is_required_and_validated_control(self):
        proposal = {'id': 'add', 'kind': 'addition', 'evidence': [self.evidence()],
                    'destination': str(self.source), 'replacement': 'Ask before publication.',
                    'reason': 'Supplied requirement', 'affected_references': [str(self.source)],
                    'expected_byte_delta': 10, 'expected_reading_change': 'Explicit approval guidance',
                    'required_decisions': [], 'observation': {
                        'provenance': 'current_supplied_session', 'detail': 'Owner supplied missing requirement',
                        'information_gap': 'Publication authority', 'utility': 'Reusable approval boundary',
                        'diff': '+Ask before publication.'}}
        result = enrich_audit(self.audit, self.assessment(proposals=[proposal]))
        self.assertEqual(result['proposals'][0]['kind'], 'addition')
        variants = []
        missing = copy.deepcopy(proposal)
        del missing['observation']
        variants.append(missing)
        for value in (None, {}):
            variants.append({**proposal, 'observation': value})
        for key in proposal['observation']:
            bad = copy.deepcopy(proposal)
            del bad['observation'][key]
            variants.append(bad)
            for value in ('', ' ', 0):
                bad = copy.deepcopy(proposal)
                bad['observation'][key] = value
                variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                enrich_audit(self.audit, self.assessment(proposals=[bad]))
        replacement = {**missing, 'kind': 'replacement'}
        self.assertEqual(enrich_audit(self.audit, self.assessment(proposals=[replacement]))['proposals'][0]['kind'],
                         'replacement')

    def test_owner_deferral_preserves_cross_report_continuity_control(self):
        decision = {'id': 'hold', 'decision': 'deferred', 'scope': [str(self.source)],
                    'provenance': 'owner message'}
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()],
            owner_decisions=[decision], dispositions=[{'finding_id': 'issue', 'status': 'owner_deferred',
                'reason': 'Owner deferred scope decision', 'owner_decision_id': 'hold'}]))
        for continued in (False, True):
            with self.subTest(continued=continued):
                after = enrich_audit(self.audit, self.assessment(findings=[self.finding('continued')] if continued else []))
                delta = compare_reports(before, after)
                self.assertEqual(delta['owner_deferred'], ['issue'])
                self.assertEqual(delta['retained' if continued else 'unresolved'], ['issue'])
                self.assertEqual(delta['new'], [])
                self.assertEqual(delta['resolved'], [])
                self.assertEqual(delta['exit_code'], 1)
        opened = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        self.assertEqual(compare_reports(opened, opened)['owner_deferred'], [])
