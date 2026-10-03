"""Remaining persisted-input shape and source-binding regressions."""
import copy
import json
import unittest
import test_reporting as fixtures
import test_reporting_edges as edge_fixtures
from reporting import enrich_audit, compare_reports, report_hash


class FinalReporting(unittest.TestCase):
    setUp = fixtures.ReportingTests.setUp
    make_audit = fixtures.ReportingTests.make_audit
    evidence = fixtures.ReportingTests.evidence
    assessment = fixtures.ReportingTests.assessment
    finding = fixtures.ReportingTests.finding
    cli = edge_fixtures.ReportingEdges.cli

    def test_consumed_nested_shapes_reject_without_traceback(self):
        for index, extras in enumerate(({"reading_summary": []}, {"chains": [0]},
            {"groups": [{"members": [0]}]}, {"graph": {"nodes": {"bad": 0}, "states": {}}})):
            with self.subTest(index=index):
                bad = copy.deepcopy(self.audit); bad.update(extras)
                path = self.root / (str(index) + ".json"); path.write_text(json.dumps(bad))
                result = self.cli("compare", "--before", path, "--after", path, "--out", self.root / (str(index) + "-out"))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_persisted_resolution_evidence_must_match_snapshot_source(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        after = enrich_audit(self.audit, self.assessment(resolves=[{
            "before_report_sha256": report_hash(before), "before_finding_id": "issue",
            "evidence": [self.evidence()], "reason": "Verified scope reconciliation"}]))
        after["resolves"][0]["evidence"][0]["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError): compare_reports(before, after)


if __name__ == "__main__":
    unittest.main()
