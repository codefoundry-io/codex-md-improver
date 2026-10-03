"""Expected IDs derive independently from the owner ledger, not product metadata."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOT = ROOT / "skills/codex-md-improver"


class RuleCoverageTests(unittest.TestCase):
    def setUp(self):
        ledger = (ROOT / "docs/design/2026-10-03-owner-decisions.md").read_text()
        included = ledger.split("### Included (107)", 1)[1].split("### Pending", 1)[0]
        self.expected = set(re.findall(r"^\| ([A-Z][A-Z0-9-]+) \|", included, re.M)) - {"ID"}
        self.rows = json.loads((SOT / "assets/criteria.json").read_text())["criteria"]

    def test_exact_independently_derived_included_set_and_unique_rows(self):
        self.assertEqual(len(self.expected), 107)
        self.assertEqual({r["id"] for r in self.rows}, self.expected)
        self.assertEqual(len(self.rows), 107)

    def test_every_nondetector_has_real_rule_group_and_tag(self):
        self.assertEqual(len(self.rows), 107)
        rules = (SOT / "references/review-rules.md").read_text()
        for row in self.rows:
            with self.subTest(rule=row["id"]):
                self.assertTrue(row["evidence"])
                self.assertTrue(row["verification"])
                self.assertTrue(row["surface"])
                self.assertTrue(row["groups"])
                if row["detector"]:
                    self.assertEqual(row["groups"], ["candidates"])
                    continue
                self.assertIn("[" + row["id"] + "]", rules)
                for group in row["groups"]:
                    self.assertIn("## " + group + "\n", rules)
                    section = rules.split("## " + group + "\n", 1)[1].split("\n## ", 1)[0]
                    self.assertIn("[" + row["id"] + "]", section)

    def test_exact_selected_detector_set_and_no_pending_rules(self):
        selected = {id for id in self.expected if id.startswith("L-")
                    and id not in {"L-REPORT", "L-SEMANTIC", "L-SCORE-DELTA"}}
        self.assertEqual(set(json.loads((SOT / "assets/defaults.json").read_text())["detector_ids"]), selected)
        actual = {r["id"] for r in self.rows if r["detector"]}
        self.assertEqual(actual, selected)
        self.assertEqual(len(actual), 17)
        self.assertFalse({"L-C0", "L-C9-BODY", "L-SCORE-PARSE", "AG24"} & {r["id"] for r in self.rows})


if __name__ == "__main__":
    unittest.main()
