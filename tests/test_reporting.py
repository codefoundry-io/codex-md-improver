"""Source-bound assessment and comparison contracts, synthetic read-only targets."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOT = Path(__file__).resolve().parents[1] / "skills/codex-md-improver"
sys.path.insert(0, str(SOT / "scripts"))
from reporting import enrich_audit, render_audit, compare_reports, score_assessment, report_hash

WEIGHTS = {"commands_workflows": 20, "structure": 20, "non_obvious_patterns": 15,
           "concision": 15, "freshness": 15, "actionability": 15}


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="codex-md-report-", dir=os.environ.get("CODEX_MD_TEST_TMP"))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.source = self.project / "AGENTS.md"
        self.source.write_text("α Require approval.\nKeep scope narrow.\n", encoding="utf-8")
        self.audit = self.make_audit()

    def make_audit(self):
        data = self.source.read_bytes()
        node = {"sha256": hashlib.sha256(data).hexdigest(), "aliases": [str(self.source)],
                "content_status": "read", "bytes": len(data)}
        return {"schema_version": 1, "scope": {"projects": [str(self.project)], "cwd": None,
                "codex_home": str(self.root / "home"), "settings": {}}, "chains": [], "groups": [],
                "graph": {"nodes": {"fixture": node}, "occurrences": [], "states": {}},
                "reading_summary": {"unique_text_bytes": len(data), "occurrences": 0, "directory_totals": {}},
                "inventory_complete": True, "text_read_complete": True,
                "semantic_review_complete": False, "partial": False, "assessment": "unassessed", "exit_code": 0}

    def evidence(self, phrase="Require approval."):
        text = self.source.read_text()
        start = text.index(phrase)
        return {"source": str(self.source), "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                "span": [start, start + len(phrase)], "text": phrase}

    def assessment(self, audit=None, **updates):
        audit = audit or self.audit
        result = {"schema_version": 1, "audit_sha256": report_hash(audit),
                  "reviewed_sources": [{"source": str(self.source), "source_sha256": self.evidence()["source_sha256"]}],
                  "semantic_review_complete": True}
        result.update(updates)
        return result

    def finding(self, id="issue", rule="C15", **updates):
        row = {"id": id, "rule_id": rule, "anchor": "approval-rule", "evidence": [self.evidence()],
               "explanation": "Approval scope conflicts with a supplied requirement.", "confidence": "high"}
        row.update(updates)
        return row

    def test_rubric_weights_earned_points_and_unassessed_total(self):
        result = score_assessment(WEIGHTS)
        self.assertEqual(result["weights"], WEIGHTS)
        self.assertEqual(result["total"], 100)
        self.assertTrue(result["complete"])
        partial = dict(WEIGHTS, structure=None)
        self.assertIsNone(score_assessment(partial)["total"])
        self.assertFalse(score_assessment({})["complete"])
        for invalid in ({"structure": 21}, {"freshness": -1}, {"concision": True},
                        {"concision": 1.5}, {"unknown": 0}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                score_assessment(invalid)

    def test_source_bound_findings_and_scores_leave_inputs_unchanged(self):
        a = self.assessment(findings=[self.finding()], dimensions={
            key: {"score": value, "evidence": [self.evidence()]} for key, value in WEIGHTS.items()})
        before = copy.deepcopy((self.audit, a))
        result = enrich_audit(self.audit, a)
        self.assertEqual((self.audit, a), before)
        self.assertEqual(result["findings"][0]["id"], "issue")
        self.assertEqual(result["rubric"]["total"], 100)
        self.assertEqual(result["exit_code"], 1)
        self.assertTrue(result["semantic_review_complete"])
        self.assertIn("Subjective", render_audit(result))

    def test_invalid_bindings_schema_ids_and_spans_reject(self):
        base = self.assessment(findings=[self.finding()])
        variants = []
        for key, value in (("schema_version", 99), ("audit_sha256", "0" * 64), ("unexpected", True)):
            x = copy.deepcopy(base); x[key] = value; variants.append(x)
        for key, value in (("rule_id", "L-C0"), ("id", ""), ("confidence", "certain")):
            x = copy.deepcopy(base); x["findings"][0][key] = value; variants.append(x)
        for key, value in (("span", [0, 900]), ("span", [True, 3]), ("text", "wrong"),
                           ("source_sha256", "0" * 64), ("source", str(self.root / "outside"))):
            x = copy.deepcopy(base); x["findings"][0]["evidence"][0][key] = value; variants.append(x)
        x = copy.deepcopy(base); x["findings"] *= 2; variants.append(x)
        for x in variants:
            with self.subTest(input=x), self.assertRaises(ValueError):
                enrich_audit(self.audit, x)

    def test_stale_source_and_metadata_only_sources_reject(self):
        a = self.assessment(findings=[self.finding()])
        self.source.write_text("changed")
        with self.assertRaises(ValueError): enrich_audit(self.audit, a)
        self.source.write_text("α Require approval.\nKeep scope narrow.\n")
        limited = copy.deepcopy(self.audit)
        limited["graph"]["nodes"]["fixture"]["content_status"] = "metadata_only"
        a["audit_sha256"] = report_hash(limited)
        with self.assertRaises(ValueError): enrich_audit(limited, a)

    def test_structured_verdict_contract(self):
        entries = [{"rule_id": "C1", "verdict": "PASS"}, {"rule_id": "C3", "verdict": "FAIL"},
                   {"rule_id": "C4", "verdict": "NA"}]
        a = self.assessment(criterion_verdicts={"schema_version": 1, "entries": entries})
        result = enrich_audit(self.audit, a)
        counts = result["verdict_summary"]
        self.assertEqual({k: counts[k] for k in ("applicable", "pass", "fail", "na", "unassessed", "pass_rate")},
                         {"applicable": 2, "pass": 1, "fail": 1, "na": 1, "unassessed": 104, "pass_rate": 0.5})
        empty = enrich_audit(self.audit, self.assessment())
        self.assertIsNone(empty["verdict_summary"]["pass_rate"])
        self.assertEqual(empty["verdict_summary"]["unassessed"], 107)
        invalid = [entries + [entries[0]], [{"rule_id": "unknown", "verdict": "PASS"}],
                   [{"rule_id": "C1", "verdict": "MAYBE"}], [{"rule_id": "C1", "verdict": "PASS", "extra": 1}]]
        for rows in invalid:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                enrich_audit(self.audit, self.assessment(criterion_verdicts={"schema_version": 1, "entries": rows}))

    def test_partial_and_overflow_remain_prominent_at_full_score(self):
        self.audit["partial"] = True
        self.audit["text_read_complete"] = False
        self.audit["chains"] = [{"cwd": str(self.project), "warning": True, "raw_volume_exceeds_budget": True,
                                  "project_original_bytes": 40000, "project_included_bytes": 32768}]
        a = self.assessment(dimensions={k: {"score": v, "evidence": [self.evidence()]} for k, v in WEIGHTS.items()})
        result = enrich_audit(self.audit, a)
        self.assertEqual(result["exit_code"], 3)
        self.assertFalse(result["semantic_review_complete"])
        rendered = render_audit(result)
        self.assertIn("partial", rendered)
        self.assertIn("overflow", rendered)
        self.assertLess(rendered.index("overflow"), rendered.index("100"))

    def test_deferrals_rejections_and_unknown_disposition(self):
        decision = {"id": "hold", "decision": "deferred", "scope": [str(self.source)], "provenance": "owner message"}
        a = self.assessment(findings=[self.finding()], owner_decisions=[decision],
            dispositions=[{"finding_id": "issue", "status": "owner_deferred", "reason": "Intentional duplication unconfirmed", "owner_decision_id": "hold"}])
        result = enrich_audit(self.audit, a)
        self.assertEqual(result["findings"][0]["status"], "owner_deferred")
        self.assertIn("Intentional duplication", render_audit(result))
        a["dispositions"][0]["finding_id"] = "missing"
        with self.assertRaises(ValueError): enrich_audit(self.audit, a)
        a["dispositions"] = [{"finding_id": "issue", "status": "rejected", "reason": "Required runtime constraint", "evidence": [self.evidence()]}]
        result = enrich_audit(self.audit, a)
        self.assertEqual(result["findings"][0]["status"], "rejected")
        self.assertIn("Required runtime constraint", render_audit(result))

    def test_compare_keeps_moved_anchor_and_unacknowledged_disappearance(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        self.source.write_text("Added heading.\nα Require approval.\nKeep scope narrow.\n")
        after_audit = self.make_audit()
        after = enrich_audit(after_audit, self.assessment(after_audit, findings=[self.finding(id="moved")]))
        delta = compare_reports(before, after)
        self.assertTrue(delta["comparable"])
        self.assertEqual(delta["retained"], ["issue"])
        self.assertEqual(delta["resolved"], [])
        self.assertGreater(delta["byte_delta"], 0)
        absent = enrich_audit(after_audit, self.assessment(after_audit))
        self.assertEqual(compare_reports(before, absent)["unresolved"], ["issue"])

    def test_explicit_resolution_binds_actual_baseline_and_complete_affected_evidence(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        after_audit = self.make_audit(); after_audit["partial"] = True
        resolves = [{"before_report_sha256": report_hash(before), "before_finding_id": "issue",
                     "evidence": [self.evidence("Keep scope narrow.")], "reason": "Reconciled the applicable scope"}]
        after = enrich_audit(after_audit, self.assessment(after_audit, resolves=resolves))
        self.assertEqual(after["resolves"][0]["baseline_validation"], "pending")
        delta = compare_reports(before, after)
        self.assertEqual(delta["resolved"], ["issue"])
        self.assertEqual(delta["exit_code"], 3)
        for key, value in (("before_report_sha256", "0" * 64), ("before_finding_id", "missing")):
            bad = copy.deepcopy(after); bad["resolves"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): compare_reports(before, bad)
        unreviewed = self.assessment(after_audit, reviewed_sources=[], resolves=resolves)
        uncertain = enrich_audit(after_audit, unreviewed)
        self.assertEqual(compare_reports(before, uncertain)["unresolved"], ["issue"])

    def test_scope_comparison_and_explicit_fail_to_pass_only(self):
        def result(rows):
            return enrich_audit(self.audit, self.assessment(criterion_verdicts={"schema_version": 1, "entries": rows}))
        before = result([{"rule_id": "C1", "verdict": "FAIL"}, {"rule_id": "C3", "verdict": "NA"}])
        after = result([{"rule_id": id, "verdict": "PASS"} for id in ("C1", "C3", "C4")])
        after["chains"] = [{"new_nested_region": True}]
        delta = compare_reports(before, after)
        self.assertTrue(delta["comparable"])
        self.assertEqual(delta["fail_to_pass"], ["C1"])
        after["scope"]["settings"] = {"trust": {str(self.project): "trusted"}}
        delta = compare_reports(before, after)
        self.assertFalse(delta["comparable"])
        self.assertEqual(delta["fail_to_pass"], [])
        self.assertEqual(delta["exit_code"], 3)

    def test_ambiguous_identity_and_owner_deferral_are_visible(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        after = enrich_audit(self.audit, self.assessment(findings=[self.finding("a"), self.finding("b")]))
        delta = compare_reports(before, after)
        self.assertEqual(delta["ambiguous"], ["issue"])
        self.assertIn("issue", delta["unresolved"])
        before["findings"][0]["status"] = "owner_deferred"
        self.assertIn("issue", compare_reports(before, after)["owner_deferred"])

    def test_proposals_new_destination_and_current_observation_requirements(self):
        proposal = {"id": "move", "kind": "replacement", "evidence": [self.evidence()],
                    "destination": str(self.project / "docs/new.md"), "replacement": "Keep approval scope explicit.",
                    "reason": "Separate focused guidance", "affected_references": [str(self.source)],
                    "expected_byte_delta": -3, "expected_reading_change": "Read only for publication", "required_decisions": []}
        result = enrich_audit(self.audit, self.assessment(proposals=[proposal]))
        self.assertEqual(result["proposals"][0]["decision_state"], "pending_new_destination")
        decision = {"id": "move-ok", "decision": "approved", "scope": [proposal["destination"]], "provenance": "owner message"}
        proposal["required_decisions"] = ["move-ok"]
        result = enrich_audit(self.audit, self.assessment(proposals=[proposal], owner_decisions=[decision]))
        self.assertEqual(result["proposals"][0]["decision_state"], "recorded_owner_approval")
        proposal.update(kind="addition", destination=str(self.source), observation={
            "provenance": "current_supplied_session", "detail": "Owner supplied missing requirement",
            "information_gap": "Publication authority", "utility": "Reusable for every publication", "diff": "+Ask before publication."})
        result = enrich_audit(self.audit, self.assessment(proposals=[proposal], owner_decisions=[decision]))
        self.assertEqual(result["proposals"][0]["kind"], "addition")
        for key, value in (("provenance", "crawled_history"), ("utility", ""), ("diff", "")):
            bad = copy.deepcopy(proposal); bad["observation"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                enrich_audit(self.audit, self.assessment(proposals=[bad], owner_decisions=[decision]))

    def test_unassessed_never_implies_pass_or_resolution(self):
        delta = compare_reports(self.audit, self.audit)
        self.assertEqual(delta["exit_code"], 0)
        self.assertEqual(delta["resolved"], [])
        self.assertIn("unassessed", render_audit(self.audit))

    def test_cli_report_compare_transport_and_unchanged_sources(self):
        audit_path = self.root / "audit.json"
        raw = json.dumps(self.audit, ensure_ascii=False, indent=3).encode()
        audit_path.write_bytes(raw)
        a = self.assessment(findings=[self.finding()]); a["audit_sha256"] = hashlib.sha256(raw).hexdigest()
        assessment_path = self.root / "assessment.json"; assessment_path.write_text(json.dumps(a))
        before_bytes = self.source.read_bytes()
        out = self.root / "report"
        args = [sys.executable, str(SOT / "scripts/md_improver.py"), "report", "--audit", str(audit_path),
                "--assessment", str(assessment_path), "--out", str(out)]
        completed = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        result = json.loads((out / "audit.json").read_text())
        self.assertEqual(result["input_audit_sha256"], a["audit_sha256"])
        self.assertEqual(self.source.read_bytes(), before_bytes)
        self.assertEqual(audit_path.read_bytes(), raw)
        delta_out = self.root / "compare"
        completed = subprocess.run([sys.executable, str(SOT / "scripts/md_improver.py"), "compare",
            "--before", str(out / "audit.json"), "--after", str(out / "audit.json"), "--out", str(delta_out)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(json.loads((delta_out / "delta.json").read_text())["comparable"])
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
