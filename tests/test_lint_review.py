"""Concrete detector boundary and evidence-retention regressions."""
import unittest
import test_lint_candidates as fixtures


class CandidateReviewTests(unittest.TestCase):
    find = fixtures.CandidateTests.find

    def test_adjacent_model_identifiers_have_exact_separate_spans(self):
        text = "Use claude-sonnet-4.5 and gpt-6.1-sol for this job."
        hits = self.find(text, "L-C8-BODY-MODEL")
        self.assertEqual([loc["text"] for h in hits for loc in h["locations"]],
                         ["claude-sonnet-4.5", "gpt-6.1-sol"])
        spaced = "Select Claude Opus 5.5 or Gemini 3.1 Pro as needed."
        hits = self.find(spaced, "L-C8-BODY-MODEL")
        self.assertEqual([loc["text"] for h in hits for loc in h["locations"]],
                         ["Claude Opus 5.5", "Gemini 3.1 Pro"])

    def test_density_counts_lines_but_retains_all_locations(self):
        text = "MUST NEVER\n" * 3 + "neutral\n" * 22
        hits = self.find(text, "L-C6")
        self.assertEqual(hits[0]["aggregate"]["count"], 3)
        self.assertEqual(len(hits[0]["locations"]), 6)
        self.assertEqual([loc["text"] for loc in hits[0]["locations"]], ["MUST", "NEVER"] * 3)

    def test_punctuated_greeting(self):
        hits = self.find("Sure! Check the input.", "L-AA2")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["locations"][0]["text"], "Sure!")


if __name__ == "__main__":
    unittest.main()
