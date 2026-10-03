"""Expose contextual limitations without conflating them with actual choices."""
import copy
import unittest
from test_recognition import answer, runtime
from recognition import evaluate_probe


class ContextReceiptTests(unittest.TestCase):
    def setUp(self):
        self.runtime = runtime()
        self.control = {"expected": answer("control"), "observed": answer("control"),
                        "delivered": True, "tool_status": "ok"}

    def evaluate(self):
        return evaluate_probe(answer(), answer(), self.control, self.runtime)

    def test_unknown_context_is_explicitly_limited(self):
        result = self.evaluate()
        self.assertEqual(result.get("status"), "recognition")
        self.assertEqual(result.get("context_status"), "limited")
        self.assertEqual(set(result.get("context_limitations", [])), {"memory_unknown", "host_guidance_unknown"})

    def test_clean_context_needs_memory_and_host_evidence(self):
        self.runtime["isolation"].update(memory="isolated", host_guidance="absent")
        self.assertEqual(self.evaluate().get("context_status"), "isolated")
        self.runtime["isolation"]["host_guidance"] = "present"
        self.assertEqual(self.evaluate().get("context_status"), "limited")

    def test_missing_invalid_host_exposure_is_invalid(self):
        for value in (None, "unverified", [], 1):
            with self.subTest(value=value):
                self.runtime["isolation"]["host_guidance"] = value
                self.assertEqual(self.evaluate().get("status"), "invalid_probe")
        del self.runtime["isolation"]["host_guidance"]
        self.assertEqual(self.evaluate().get("status"), "invalid_probe")


if __name__ == "__main__":
    unittest.main()
