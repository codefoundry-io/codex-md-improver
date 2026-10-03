"""Source-review regressions for assessment context and comparison contracts."""
import copy
import hashlib
import json
import unittest
import test_reporting as fixtures
import test_reporting_edges as edge_fixtures
from reporting import enrich_audit, compare_reports


class ReportingReview(unittest.TestCase):
    setUp = fixtures.ReportingTests.setUp
    make_audit = fixtures.ReportingTests.make_audit
    evidence = fixtures.ReportingTests.evidence
    assessment = fixtures.ReportingTests.assessment
    finding = fixtures.ReportingTests.finding
    cli = edge_fixtures.ReportingEdges.cli

    def test_evidence_scenario_requires_reachable_alias(self):
        self.audit["chains"] = [{"scenario_id": "A"}, {"scenario_id": "B"}]
        self.audit["graph"]["states"] = {"A|" + str(self.source): {
            "path": str(self.source), "kind": "leaf", "identity": "fixture", "children": []}}
        finding = self.finding()
        finding["evidence"][0]["scenario_id"] = "A"
        self.assertEqual(enrich_audit(self.audit, self.assessment(findings=[finding]))["findings"][0]["id"], "issue")
        finding["evidence"][0]["scenario_id"] = "B"
        with self.assertRaises(ValueError): enrich_audit(self.audit, self.assessment(findings=[finding]))

    def test_existing_proposal_destination_and_affected_reference_revalidate(self):
        target = self.project / "other.md"; target.write_text("Original context.")
        self.audit["graph"]["nodes"]["other"] = {"aliases": [str(target)], "bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "content_status": "read"}
        proposal = {"id": "addition", "kind": "addition", "evidence": [self.evidence()],
            "destination": str(target), "replacement": "Add reusable guidance.", "reason": "Current information gap",
            "affected_references": [], "expected_byte_delta": 12, "expected_reading_change": "No extra reference",
            "required_decisions": [], "observation": {"provenance": "current_supplied_session", "detail": "owner input",
                "information_gap": "Missing rule", "utility": "Recurring operation", "diff": "+Add reusable guidance."}}
        target.write_text("Changed after scan.")
        with self.assertRaises(ValueError): enrich_audit(self.audit, self.assessment(proposals=[proposal]))
        proposal.update(destination=str(self.source), affected_references=[str(target)])
        with self.assertRaises(ValueError): enrich_audit(self.audit, self.assessment(proposals=[proposal]))

    def test_cli_rejects_invalid_comparison_schema_and_unknown_verdict(self):
        cases = [dict(self.audit, schema_version=True), dict(self.audit, scope=[]),
                 dict(self.audit, criterion_verdicts={"NOT-A-RULE": "FAIL"}), dict(self.audit, findings="bad")]
        for index, before in enumerate(cases):
            with self.subTest(index=index):
                path = self.root / (str(index) + ".json"); path.write_text(json.dumps(before))
                result = self.cli("compare", "--before", path, "--after", path, "--out", self.root / (str(index) + "-out"))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_rejected_baseline_is_not_resurrected_as_open(self):
        a = self.assessment(findings=[self.finding()], dispositions=[{"finding_id": "issue", "status": "rejected",
            "reason": "Valid operational constraint", "evidence": [self.evidence()]}])
        before = enrich_audit(self.audit, a)
        after = enrich_audit(self.audit, self.assessment())
        delta = compare_reports(before, after)
        self.assertEqual(delta["unresolved"], [])
        self.assertEqual(delta["exit_code"], 0)
        self.assertEqual(delta.get("rejected"), ["issue"])

    def test_duplicate_baseline_identity_stays_ambiguous(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding("first"), self.finding("second")]))
        after = enrich_audit(self.audit, self.assessment(findings=[self.finding("after")]))
        delta = compare_reports(before, after)
        self.assertEqual(delta["retained"], [])
        self.assertEqual(delta["ambiguous"], ["first", "second"])
        self.assertEqual(delta["unresolved"], ["first", "second"])

    def test_compare_preserves_scanner_candidates_and_loader_warning(self):
        candidate = {"rule_id": "L-C8-BODY-DATE", "path": str(self.source), "classification": "heuristic_candidate"}
        for extras in ({"candidates": [candidate]}, {"chains": [{"warning": True, "raw_volume_exceeds_budget": False}]}):
            with self.subTest(extras=extras):
                report = copy.deepcopy(self.audit); report.update(extras, exit_code=1)
                delta = compare_reports(report, report)
                self.assertEqual(delta["exit_code"], 1)
                self.assertTrue(delta.get("remaining_scan_findings"))

    def test_shadowed_guidance_does_not_get_reference_only_toc(self):
        self.source.write_text("Ordinary instruction.\n" * 101)
        (self.project / "AGENTS.override.md").write_text("Selected instruction.\n")
        home = self.root / "home"; home.mkdir()
        settings = self.root / "settings.json"; settings.write_text(json.dumps({"trust": {str(self.project): "trusted"}}))
        out = self.root / "scan"
        result = self.cli("scan", "--project", self.project, "--cwd", self.project,
            "--codex-home", home, "--settings", settings, "--out", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        audit = json.loads((out / "audit.json").read_text())
        self.assertFalse(any(c["rule_id"] == "L-C9-TOC" for c in audit["candidates"]))


if __name__ == "__main__":
    unittest.main()
