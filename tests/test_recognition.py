"""Controlled choices and invalid-delivery behavior, independent of providers."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/codex-md-improver/scripts"))
from recognition import evaluate_probe


def answer(case="publication", sources=None, action="read_release_rules"):
    return {"case_id": case, "selected_sources": sources or ["release.md"],
            "scope": "project", "next_action": action, "unresolved": []}


def runtime():
    return {"source_hash": "a" * 64, "packet_hash": "b" * 64,
            "requested": {"model": "Sol", "effort": "medium"},
            "resolved": {"model": "test-model", "effort": "medium"},
            "effective": {"model": None, "effort": None, "status": "UNEXPOSED"},
            "client_version": "test-client", "delivered": True, "tool_status": "ok",
            "isolation": {"fork_turns": "none", "history": "none", "memory": "unknown",
                          "target_guidance": "present", "host_guidance": "unknown"},
            "tool_constraints": {"containment": "prompt_only", "detail": "No tool calls requested."}}


class RecognitionTests(unittest.TestCase):
    def setUp(self):
        self.expected = answer()
        self.control = {"expected": answer("control", ["guide.md"]),
                        "observed": answer("control", ["guide.md"]),
                        "delivered": True, "tool_status": "ok"}
        self.runtime = runtime()

    def evaluate(self, observed=None, **changes):
        return evaluate_probe(changes.get("expected", self.expected),
                              self.expected if observed is None else observed,
                              changes.get("control", self.control), changes.get("runtime", self.runtime))

    def test_match_retains_full_receipt_and_does_not_authorize_revision(self):
        result = self.evaluate()
        self.assertEqual(result.get("status"), "recognition")
        self.assertFalse(result["revision_eligible"])
        for key in ("case_id", "expected", "observed", "mismatch", "control_result",
                    "isolation", "source_hash", "packet_hash", "requested", "resolved",
                    "effective", "client_version", "tool_constraints"):
            self.assertIn(key, result)
        self.assertIsNone(result["effective"]["model"])
        self.assertEqual(result["isolation"]["memory"], "unknown")

    def test_mismatch_is_bounded_choice_evidence(self):
        observed = answer(sources=["background.md"], action="skip")
        result = self.evaluate(observed)
        self.assertEqual(result.get("status"), "nonrecognition")
        self.assertTrue(result["revision_eligible"])
        self.assertEqual(set(result["mismatch"]), {"selected_sources", "next_action"})

    def test_set_choices_ignore_order_but_duplicates_are_invalid(self):
        expected = answer(sources=["a.md", "b.md"])
        self.assertEqual(self.evaluate(answer(sources=["b.md", "a.md"]), expected=expected).get("status"), "recognition")
        self.assertEqual(self.evaluate(answer(sources=["a.md", "a.md"])).get("status"), "invalid_probe")

    def test_wrong_case_and_answer_shapes_are_invalid(self):
        variants = [answer("wrong"), [], None, {"case_id": "publication"},
                    dict(answer(), selected_sources="release.md"), dict(answer(), unresolved=[False]),
                    dict(answer(), scope=""), dict(answer(), next_action=1), dict(answer(), unexpected=True)]
        for observed in variants:
            with self.subTest(observed=observed):
                result = evaluate_probe(self.expected, observed, self.control, self.runtime)
                self.assertEqual(result.get("status"), "invalid_probe")
                self.assertFalse(result["revision_eligible"])

    def test_control_failures_invalidate_even_an_expected_match(self):
        for control in (None, {}, dict(self.control, delivered=False),
                        dict(self.control, tool_status="denied"),
                        dict(self.control, observed=answer("wrong")),
                        dict(self.control, observed=answer("control", ["wrong.md"]))):
            with self.subTest(control=control):
                result = self.evaluate(control=control)
                self.assertEqual(result.get("status"), "invalid_probe")
                self.assertFalse(result["revision_eligible"])

    def test_missing_delivery_or_runtime_metadata_is_invalid(self):
        for key in self.runtime:
            value = copy.deepcopy(self.runtime)
            value.pop(key)
            with self.subTest(key=key):
                self.assertEqual(self.evaluate(runtime=value).get("status"), "invalid_probe")
        for value in (None, [], dict(self.runtime, delivered=False), dict(self.runtime, delivered=1),
                      dict(self.runtime, tool_status="failed"), dict(self.runtime, source_hash="bad"),
                      dict(self.runtime, packet_hash="x" * 64)):
            self.assertEqual(self.evaluate(runtime=value).get("status"), "invalid_probe")

    def test_isolation_selectors_and_tool_constraints_are_checked(self):
        changes = [("isolation", {"fork_turns": "all", "history": "inherited", "memory": "unknown", "target_guidance": "present"}),
                   ("requested", {"model": "Sol", "effort": "high"}),
                   ("resolved", {"model": "", "effort": "medium"}),
                   ("resolved", {"model": "test-model", "effort": "low"}),
                   ("effective", {"model": None, "effort": None}),
                   ("effective", {"model": "other-model", "effort": "low", "status": "EXPOSED"}),
                   ("tool_constraints", {"containment": "unknown"}),
                   ("isolation", {"fork_turns": "none", "history": "none", "memory": "unknown", "target_guidance": "absent"})]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                self.assertEqual(self.evaluate(runtime=dict(self.runtime, **{key: value})).get("status"), "invalid_probe")

    def test_valid_exposed_identity_is_separate_from_requested(self):
        value = copy.deepcopy(self.runtime)
        value["effective"] = dict(value["resolved"], status="EXPOSED")
        value["tool_constraints"]["containment"] = "enforced"
        value["isolation"]["memory"] = "isolated"
        self.assertEqual(self.evaluate(runtime=value).get("status"), "recognition")

    def test_inputs_and_receipts_are_independent(self):
        before = copy.deepcopy((self.expected, self.control, self.runtime))
        result = self.evaluate()
        self.assertEqual(result.get("status"), "recognition")
        result["observed"]["selected_sources"].append("new")
        self.assertEqual((self.expected, self.control, self.runtime), before)

    def test_scenario_catalog_shapes(self):
        cases = json.loads((ROOT / "tests/recognition-cases.json").read_text())
        self.assertEqual(len({c["input"]["case_id"] for c in cases}), len(cases))
        self.assertGreaterEqual(len(cases), 12)
        for case in cases:
            result = self.evaluate(case["expected"], expected=case["expected"])
            self.assertEqual(result.get("status"), "recognition", case["input"]["case_id"])
            self.assertNotIn("expected", case["input"])


if __name__ == "__main__":
    unittest.main()
