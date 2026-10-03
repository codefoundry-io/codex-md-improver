"""Transport and aggregate controls distinguished during test preflight."""
import hashlib
import json
import subprocess
import sys
import unittest
import test_reporting as fixtures
from reporting import enrich_audit, compare_reports, report_hash


class ReportingEdges(unittest.TestCase):
    setUp = fixtures.ReportingTests.setUp
    make_audit = fixtures.ReportingTests.make_audit
    evidence = fixtures.ReportingTests.evidence
    assessment = fixtures.ReportingTests.assessment
    finding = fixtures.ReportingTests.finding

    def test_verdict_subrecord_invalid_shapes_and_all_na(self):
        for value in ({"schema_version": 2, "entries": []}, {"schema_version": 1, "entries": [], "extra": 1},
                      {"schema_version": 1, "entries": {}}, {"schema_version": 1, "entries": [42]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                enrich_audit(self.audit, self.assessment(criterion_verdicts=value))
        result = enrich_audit(self.audit, self.assessment(criterion_verdicts={"schema_version": 1,
            "entries": [{"rule_id": "C1", "verdict": "NA"}, {"rule_id": "C3", "verdict": "NA"}]}))
        summary = result["verdict_summary"]
        self.assertEqual((summary["applicable"], summary["na"], summary["unassessed"], summary["pass_rate"]), (0, 2, 105, None))

    def test_complete_resolved_only_delta(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        after = enrich_audit(self.audit, self.assessment(resolves=[{
            "before_report_sha256": report_hash(before), "before_finding_id": "issue",
            "evidence": [self.evidence()], "reason": "Confirmed the explicit owner scope"}]))
        delta = compare_reports(before, after)
        self.assertEqual(delta["resolved"], ["issue"])
        self.assertEqual(delta["exit_code"], 0)

    def cli(self, command, *args):
        return subprocess.run([sys.executable, str(fixtures.SOT / "scripts/md_improver.py"), command, *map(str, args)],
                              capture_output=True, text=True)

    def test_cli_resolves_actual_file_hash_and_rejects_canonical_substitute(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        before_path = self.root / "before.json"
        before_raw = json.dumps(before, ensure_ascii=False, indent=4).encode()
        before_path.write_bytes(before_raw)
        baseline_hash = hashlib.sha256(before_raw).hexdigest()
        self.assertNotEqual(baseline_hash, report_hash(before))
        audit_path = self.root / "scan.json"
        raw = json.dumps(self.audit).encode(); audit_path.write_bytes(raw)
        for label, digest, expected in (("valid", baseline_hash, 0), ("wrong", report_hash(before), 2)):
            a = self.assessment(resolves=[{"before_report_sha256": digest, "before_finding_id": "issue",
                "evidence": [self.evidence()], "reason": "Owner clarified scope"}])
            a["audit_sha256"] = hashlib.sha256(raw).hexdigest()
            a_path = self.root / (label + ".json"); a_path.write_text(json.dumps(a))
            out = self.root / (label + "-report")
            completed = self.cli("report", "--audit", audit_path, "--assessment", a_path, "--out", out)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            delta_out = self.root / (label + "-delta")
            completed = self.cli("compare", "--before", before_path, "--after", out / "audit.json", "--out", delta_out)
            self.assertEqual(completed.returncode, expected, completed.stderr)
            if expected == 0:
                self.assertEqual(json.loads((delta_out / "delta.json").read_text())["resolved"], ["issue"])

    def test_cli_declared_unresolved_semantics_is_partial(self):
        path = self.root / "audit.json"; raw = json.dumps(self.audit).encode(); path.write_bytes(raw)
        a = self.assessment(semantic_review_complete=False)
        a["audit_sha256"] = hashlib.sha256(raw).hexdigest()
        a_path = self.root / "assessment.json"; a_path.write_text(json.dumps(a))
        result = self.cli("report", "--audit", path, "--assessment", a_path, "--out", self.root / "report")
        self.assertEqual(result.returncode, 3, result.stderr)

    def test_scan_includes_candidates_with_source_binding(self):
        self.source.write_text("The preferred version changed on 2026-09-12.\n")
        home = self.root / "home"; home.mkdir()
        settings = self.root / "settings.json"
        settings.write_text(json.dumps({"trust": {str(self.project): "trusted"}}))
        out = self.root / "scan-out"
        result = self.cli("scan", "--project", self.project, "--cwd", self.project, "--codex-home", home,
                          "--settings", settings, "--out", out)
        self.assertEqual(result.returncode, 1, result.stderr)
        audit = json.loads((out / "audit.json").read_text())
        hits = [c for c in audit["candidates"] if c["rule_id"] == "L-C8-BODY-DATE"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["source_sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertIn("heuristic", (out / "audit.md").read_text())


if __name__ == "__main__":
    unittest.main()
