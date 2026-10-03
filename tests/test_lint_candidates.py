"""Selected candidate contracts: hand-authored fixtures, no legacy implementation."""
import json
from pathlib import Path
import sys
import unittest

SOT = Path(__file__).resolve().parents[1] / "skills/codex-md-improver"
sys.path.insert(0, str(SOT / "scripts"))
from lint_candidates import find_candidates

IDS = {
    "L-C8-BODY-DATE", "L-C8-BODY-YEAR", "L-C8-BODY-SEMVER",
    "L-C8-BODY-TOOLVER", "L-C8-BODY-MODEL", "L-C8-BODY-RECENCY",
    "L-C6", "L-C4-EXCUSES", "L-C4-NARRATIVE", "L-C10", "L-C9-TOC",
    "L-C3", "L-AA1", "L-AA2", "L-AA3", "L-AA5", "L-AA6",
}


class CandidateTests(unittest.TestCase):
    def find(self, text, rule, kind="agents_guidance"):
        return find_candidates(text, Path("AGENTS.md"), kind, {rule})

    def test_positive_branches_and_record_contract(self):
        positives = {
            "L-C8-BODY-DATE": "The model changed on 2026-09-12.",
            "L-C8-BODY-YEAR": "Since 2025, this tool handles requests.",
            "L-C8-BODY-SEMVER": "The preferred tool version is v1.2.3.",
            "L-C8-BODY-TOOLVER": "We rely on Python 3.12 behavior.",
            "L-C8-BODY-MODEL": "Use gpt-6.1-sol for this job.",
            "L-C8-BODY-RECENCY": "Use the newly released feature.",
            "L-C6": "MUST check! NEVER skip!\n" * 3 + "Run checks.\n" * 22,
            "L-C4-EXCUSES": "Do not skip because it is trivial or because it takes too long.",
            "L-C4-NARRATIVE": "The model kept forgetting to close the handle.",
            "L-C10": "Do not skip; never guess; don't ignore.\n" + "Run checks.\n" * 24,
            "L-C9-TOC": "Details.\n" * 101,
            "L-C3": "The service price is $20 per month.",
            "L-AA1": "Use the file we discussed.",
            "L-AA2": "Great question! I will help you.",
            "L-AA3": "You might want to consider maybe checking inputs.",
            "L-AA5": "🚀✨🔥 Important announcement!",
            "L-AA6": "설정 파일을 확인하고 결과를 알려 주세요.",
        }
        for rule, text in positives.items():
            with self.subTest(rule=rule):
                kind = "markdown_reference" if rule == "L-C9-TOC" else "agents_guidance"
                hits = self.find(text, rule, kind)
                self.assertTrue(hits, rule)
                for hit in hits:
                    self.assertEqual(hit["rule_id"], rule)
                    self.assertEqual(hit["document_kind"], kind)
                    self.assertEqual(hit["path"], "AGENTS.md")
                    self.assertEqual(hit["classification"], "heuristic_candidate")
                    self.assertTrue(hit["explanation"])
                    self.assertTrue(hit["parameters"]["language_limit"])
                    self.assertTrue(hit["exceptions"])
                    self.assertNotIn("verdict", hit)
                    self.assertTrue(hit["locations"] or hit["aggregate"])
                    for loc in hit["locations"]:
                        self.assertEqual(text[loc["start"]:loc["end"]], loc["text"])
                json.dumps(hits)

    def test_branch_exception_controls(self):
        negatives = {
            "L-C8-BODY-DATE": "Use the runtime date argument.",
            "L-C8-BODY-YEAR": "The fixture has 2025 rows.",
            "L-C8-BODY-SEMVER": "Select the supported tool release.",
            "L-C8-BODY-TOOLVER": "Run the configured interpreter.",
            "L-C8-BODY-MODEL": "Select the configured model.",
            "L-C8-BODY-RECENCY": "Read the current file contents.",
            "L-C6": "Use the input.\n" * 25,
            "L-C4-EXCUSES": "Close the handle after reading to avoid leaking descriptors.",
            "L-C4-NARRATIVE": "Retry on timeout; return the last error if the retry fails.",
            "L-C10": "Do not refactor beyond this task.\n" + "Use the input.\n" * 24,
            "L-C9-TOC": "# Table of contents\n- [Details](#details)\n" + "Details.\n" * 101,
            "L-C3": "Use the configured project endpoint for requests.",
            "L-AA1": "Analyze the path supplied by the runtime user.",
            "L-AA2": "Validate the input and report the result.",
            "L-AA3": "Record uncertainty when the evidence is incomplete.",
            "L-AA5": "## Inputs\n- **path**: source file\n",
            "L-AA6": "Audience: Korean-speaking users.\n설정 파일을 확인하세요.",
        }
        for rule, text in negatives.items():
            with self.subTest(rule=rule):
                kind = "markdown_reference" if rule == "L-C9-TOC" else "agents_guidance"
                self.assertEqual(self.find(text, rule, kind), [])

    def test_exact_allowlist_no_pending_branches(self):
        defaults = json.loads((SOT / "assets/defaults.json").read_text())
        self.assertEqual(set(defaults.get("detector_ids", [])), IDS)
        text = "---\ndescription: 2026-09-12 gpt-6.1-sol\n---\n" + "Body\n" * 201
        for rule in ("L-C0", "L-C8-DESC-DATE", "L-C9-BODY", "L-KIND", "L-SCORE-PARSE"):
            self.assertEqual(self.find(text, rule), [])
        self.assertEqual(find_candidates("2026-09-12", Path("x"), "agents_guidance", set()), [])

    def test_guidance_only_and_reference_toc_only(self):
        text = "MUST NEVER use gpt-6.1-sol as you requested. 🚀\n" * 101
        for kind in ("code_config", "binary", "skill_excluded"):
            self.assertEqual(find_candidates(text, Path("x"), kind, IDS), [])
        self.assertEqual(self.find("Body\n" * 101, "L-C9-TOC"), [])
        self.assertTrue(self.find("2026-09-12", "L-C8-BODY-DATE", "linked_instruction"))

    def test_frontmatter_and_crlf_keep_original_unicode_spans(self):
        text = "---\r\ndescription: 2025-01-01\r\n---\r\nα: 2026-09-12\r\n"
        hits = self.find(text, "L-C8-BODY-DATE")
        self.assertEqual(len(hits), 1)
        loc = hits[0]["locations"][0]
        self.assertEqual(loc["line"], 4)
        self.assertEqual(loc["start"], text.index("2026"))
        self.assertEqual(loc["text"], "2026-09-12")

    def test_density_minimum_strict_boundary_and_distinct_counting(self):
        for length, count, expect in ((24, 24, False), (25, 2, False), (25, 3, True),
                                      (100, 8, False), (100, 9, True)):
            with self.subTest(length=length, count=count):
                c6 = "MUST NEVER\n" * count + "neutral\n" * (length - count)
                c10 = "never\n" * count + "neutral\n" * (length - count)
                for rule, text in (("L-C6", c6), ("L-C10", c10)):
                    hits = self.find(text, rule)
                    self.assertEqual(bool(hits), expect)
                    if expect:
                        self.assertEqual(hits[0]["aggregate"]["count"], count)
                        self.assertEqual(hits[0]["aggregate"]["body_lines"], length)
                        self.assertEqual(hits[0]["parameters"]["minimum_body_lines"], 25)
        line = "MUST NEVER MANDATORY; do not; don't\n" + "neutral\n" * 24
        self.assertEqual(self.find(line, "L-C6"), [])
        hits = self.find(line, "L-C10")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["aggregate"]["count"], 3)

    def test_all_locations_survive_json(self):
        text = "2026-09-12 and 2026-09-13\n" * 9
        hits = json.loads(json.dumps(self.find(text, "L-C8-BODY-DATE")))
        self.assertEqual(sum(len(h["locations"]) for h in hits), 18)

    def test_runtime_command_and_semantic_exceptions_preserved(self):
        cases = [
            ("L-C8-BODY-MODEL", "Run `tool --model gpt-6.1-sol` exactly.", "exact command"),
            ("L-C8-BODY-SEMVER", "Run `tool --version 1.2.3` exactly.", "exact command"),
            ("L-C8-BODY-TOOLVER", "Requires Python 3.12 to parse the input.", "runtime requirement"),
            ("L-C8-BODY-DATE", "Pass 2026-10-03 as the runtime date argument.", "runtime date"),
            ("L-C8-BODY-RECENCY", "Use the latest release only when testing freshness.", "operational condition"),
            ("L-C3", "Read the price before calculating the request cost.", "necessary project"),
            ("L-C4-EXCUSES", 'Recognize "because it is trivial" as a quoted excuse.', "hazard recognition"),
            ("L-C4-NARRATIVE", 'Example: "the model kept forgetting the input".', "quoted example"),
            ("L-AA1", 'Example: "as you requested".', "quoted example"),
            ("L-AA2", 'Recognize the input "Great question!".', "quoted example"),
            ("L-AA3", "You might want to consider the uncertain evidence.", "meaningful uncertainty"),
            ("L-AA5", "Legend: 🚀 means deployment starts.", "functional formatting"),
            ("L-AA6", "설정 파일을 확인하세요.", "audience unknown"),
        ]
        for rule, text, exception in cases:
            with self.subTest(rule=rule):
                original = text[:]
                hits = self.find(text, rule)
                self.assertTrue(hits)
                self.assertTrue(any(exception in e for h in hits for e in h["exceptions"]))
                self.assertEqual(text, original)

    def test_fenced_code_and_quoted_language_are_not_guidance(self):
        text = "```text\n2026-09-12 MUST NEVER 🚀\n```\n" + "neutral\n" * 25
        self.assertEqual(find_candidates(text, Path("AGENTS.md"), "agents_guidance", IDS), [])
        self.assertEqual(self.find('Trigger: "설정 확인".\nUse `한글` as the exact identifier.', "L-AA6"), [])

    def test_reference_threshold_and_fenced_toc_is_not_evidence(self):
        self.assertEqual(self.find("detail\n" * 100, "L-C9-TOC", "markdown_reference"), [])
        text = "```\n# Table of contents\n```\n" + "detail\n" * 101
        self.assertTrue(self.find(text, "L-C9-TOC", "markdown_reference"))


if __name__ == "__main__":
    unittest.main()
