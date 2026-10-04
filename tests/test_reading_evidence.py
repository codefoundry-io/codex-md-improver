"""V2 visible-evidence contract; earlier RED files remain immutable evidence.

Tables may add columns/reorder columns. Required labels identify evidence and
scenario context. CR/LF/U+2028/U+2029 are displayed as literal backslash escapes;
backslash, pipe and HTML are encoded safely in every untrusted cell.
"""
import copy
import html
import re
import unittest
import reading_report_fixtures as fixtures
from reporting import render_audit


def tables(rendered):
    """Independent small Markdown-table reader, permitting extra columns."""
    result, header = [], None
    for line in rendered.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            header = None
            continue
        # A delimiter is unescaped only with an even number of preceding slashes.
        cells, current, slashes = [], "", 0
        for char in line[1:-1]:
            if char == "|" and slashes % 2 == 0:
                cells.append(current)
                current = ""
            else:
                current += char
            slashes = slashes + 1 if char == "\\" else 0
        cells.append(current)
        if all(re.fullmatch(r"\s*:?-+:?\s*", cell) for cell in cells):
            continue
        decoded = [html.unescape(re.sub(r"\\([\\|])", r"\1", cell.strip().strip("`")))
                   for cell in cells]
        if header is None:
            header = decoded
        else:
            if len(decoded) != len(header):
                raise AssertionError("Table evidence must remain one physical row with valid cells")
            result.append(dict(zip(header, decoded)))
    return result


def displayed(value):
    return str(value).replace("\r", r"\r").replace("\n", r"\n").replace("\u2028", r"\u2028").replace("\u2029", r"\u2029")


class ReadingReportV2(unittest.TestCase):
    setUp = fixtures.ReadingReportRegressionTests.setUp
    put = fixtures.ReadingReportRegressionTests.put
    source_text = fixtures.ReadingReportRegressionTests.source_text
    chain = fixtures.ReadingReportRegressionTests.chain
    report = fixtures.ReadingReportRegressionTests.report

    def scenarios(self, included=(113, 127)):
        result = []
        for index, amount in enumerate(included):
            cwd = self.root / ("cwd-alpha" if index == 0 else "cwd-beta")
            cwd.mkdir(exist_ok=True)
            chain = self.chain("alpha" if index == 0 else "beta", amount, cwd)
            chain["partial"] = amount is None
            result.append(chain)
        return result

    def rendered_rows(self, report):
        return tables(render_audit(report))

    def metrics(self, rows, size, count, status):
        for label, value in (("Known unique reachable text bytes", size),
                             ("Physical readable text files", count)):
            matches = [row for row in rows if row.get("Metric") == label]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["Measured value"], str(value))
            self.assertEqual(matches[0]["Status"], status)

    def loader(self, rows, chain, group=""):
        matches = [row for row in rows if "Loader original bytes" in row
                   and row.get("Scenario ID") == displayed(chain["scenario_id"])]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        self.assertEqual(row["Cwd"], displayed(chain["cwd"]))
        self.assertEqual(row["Environment group"], displayed(group))
        self.assertEqual(row["Loader original bytes"], str(chain["project_original_bytes"]))
        self.assertEqual(row["Loader included bytes"], "unknown" if chain["project_included_bytes"] is None
                         else str(chain["project_included_bytes"]))

    def test_complete_reading_and_distinct_loader_cwd_group_identity(self):
        self.source_text("[first](first.md)\n[second](second.md)\n")
        self.put("first.md", "a" * 59)
        self.put("second.md", "b" * 73)
        chains = self.scenarios()
        chains[1]["environment_group_id"] = "group-beta"
        chains[1]["scenario_id"] = "group:group-beta:beta"
        report = self.report(chains)
        # Production group records contain full chain dictionaries in members.
        report["chains"] = [chains[0]]
        report["groups"] = [{"id": "group-beta", "members": [chains[1]], "limit": 32768,
                             "project_original_bytes": 137, "project_included_bytes": 127,
                             "warning": False, "raw_volume_exceeds_budget": False,
                             "global_candidate_bytes": 0, "delivered_bytes": None,
                             "delivery": "conditional_on_runtime_permissions", "possible_outcomes": ["assembled"]}]
        before = copy.deepcopy(report)
        rows = self.rendered_rows(report)
        self.loader(rows, chains[0])
        self.loader(rows, chains[1], "group-beta")
        self.metrics(rows, 269, 3, "complete")
        self.assertEqual(report, before)

    def test_multiple_unresolved_scenarios_keep_full_identity_and_lower_bound(self):
        condition = "Read `docs/uncounted.md` when building."
        self.source_text("[known](known.md)\n" + condition + "\n")
        self.put("known.md", "k" * 59)
        self.put("docs/uncounted.md", "unresolved candidate")
        chains = self.scenarios((None, None))
        report = self.report(chains)
        before = copy.deepcopy(report)
        rows = self.rendered_rows(report)
        self.metrics(rows, 196, 2, "lower bound")
        unresolved = [edge for edge in report["graph"]["occurrences"] if edge["status"] == "unresolved"]
        self.assertEqual(len(unresolved), 2)
        visible = [row for row in rows if row.get("Target") == "docs/uncounted.md"]
        self.assertEqual(len(visible), len(unresolved))
        self.assertEqual([row["Scenario ID"] for row in visible], [chain["scenario_id"] for chain in chains])
        for chain in chains:
            self.loader(rows, chain)
            row = next(row for row in visible if row["Scenario ID"] == chain["scenario_id"])
            edge = next(edge for edge in unresolved if edge["scenario_id"] == chain["scenario_id"])
            self.assertEqual(row["Cwd"], chain["cwd"])
            self.assertEqual(row["Source"], str(self.source))
            self.assertEqual(row["Classification"], "read_dependency")
            self.assertEqual(row["Condition"], condition)
            self.assertEqual({part.strip().strip("`") for part in row["Base alternatives"].split("<br>")},
                             set(edge["alternatives"]))
        self.assertEqual(report, before, "Full graph records remain unchanged for audit.json")

    def test_directory_summaries_show_scenario_cwd_bytes_and_partial_status(self):
        self.source_text("[docs](docs/)\n")
        self.put("docs/a.md", "a" * 23)
        chains = self.scenarios()
        for partial in (False, True):
            with self.subTest(partial=partial):
                prefix = "Read `missing.md`.\n" if partial else ""
                self.put("docs/b.md", prefix + "b" * (41 - len(prefix)))
                report = self.report(chains)
                summaries = report["reading_summary"]["directory_summaries_by_scenario"]
                self.assertEqual(set(summaries), {"alpha", "beta"})
                rows = [row for row in self.rendered_rows(report) if "Directory" in row]
                self.assertEqual(len(rows), 2)
                self.assertEqual([row["Scenario ID"] for row in rows], ["alpha", "beta"])
                for chain, row in zip(chains, rows):
                    summary = summaries[chain["scenario_id"]][str(self.root / "docs")]
                    self.assertEqual(summary["unique_text_bytes"], 64)
                    self.assertEqual(summary["physical_text_files"], 2)
                    self.assertEqual(summary["lower_bound"], partial)
                    self.assertEqual(row["Cwd"], chain["cwd"])
                    self.assertEqual(row["Directory"], str(self.root / "docs"))
                    self.assertEqual(row["Known unique reachable text bytes"], "64")
                    self.assertEqual(row["Physical readable text files"], "2")
                    self.assertEqual(row["Status"], "lower bound" if partial else "complete")

    def test_inventory_or_chain_partial_is_lower_bound_but_route_cap_alone_is_complete(self):
        self.source_text("[first](first.md)\n[second](second.md)\n")
        self.put("first.md", "a" * 59)
        self.put("second.md", "b" * 73)
        original = self.report(self.scenarios())
        self.assertFalse(original["graph"]["partial"])
        for reason in ("inventory", "chain", "route_cap", "cap_and_graph", "cap_and_inventory", "group_member", "unknown_loader"):
            with self.subTest(reason=reason):
                report = copy.deepcopy(original)
                report["partial"] = True
                if reason == "inventory":
                    report["inventory_complete"] = False
                elif reason == "chain":
                    report["chains"][0]["partial"] = True
                elif reason == "group_member":
                    member = report["chains"].pop()
                    member["partial"] = True
                    report["groups"] = [{"id": "partial-group", "members": [member]}]
                elif reason == "unknown_loader":
                    report["chains"][0].update(project_included_bytes=None, partial=True)
                else:
                    report["route_limit_reached"] = True
                    if reason == "cap_and_graph":
                        report["graph"]["partial"] = True
                    elif reason == "cap_and_inventory":
                        report["inventory_complete"] = False
                self.metrics(self.rendered_rows(report), 269, 3,
                             "complete" if reason == "route_cap" else "lower bound")

    def test_all_untrusted_table_cells_escape_backslash_pipe_HTML_and_line_separators(self):
        self.source_text("Read `docs/uncounted.md` when building.\n")
        report = self.report(self.scenarios((None, None)))
        # Existing public fields may contain persisted untrusted text beyond _lex's
        # single-line conditions. Vary every displayed identity/evidence field.
        hostile = "literal\\path|<b>text</b>\r\nnext\u2028line\u2029end"
        for chain in report["chains"]:
            chain["scenario_id"] += hostile
            chain["cwd"] += hostile
            chain["environment_group_id"] = hostile
        for index, edge in enumerate(report["graph"]["occurrences"]):
            edge["scenario_id"] = report["chains"][index]["scenario_id"]
            edge["cwd"] = report["chains"][index]["cwd"]
            edge["source"] += hostile
            edge["target_text"] += hostile
            edge["condition"] = "| Read | " + hostile + " |"
            edge["alternatives"] = ["first" + hostile, "second" + hostile]
        # Directory fields have the same escaping contract, with existing schema.
        report["reading_summary"]["directory_summaries_by_scenario"] = {
            chain["scenario_id"]: {str(self.root / "docs") + hostile: {
                "unique_text_bytes": 64, "physical_text_files": 2, "lower_bound": True,
                "read_conditions": [], "frontiers": [], "frontier_counts": {}}}
            for chain in report["chains"]}
        before = copy.deepcopy(report)
        rendered = render_audit(report)
        rows = tables(rendered)
        self.assertNotIn("<b>", rendered)
        self.assertNotIn("</b>", rendered)
        self.assertNotIn("\r", rendered)
        self.assertNotIn("\u2028", rendered)
        self.assertNotIn("\u2029", rendered)
        for chain, edge in zip(report["chains"], report["graph"]["occurrences"]):
            self.loader(rows, chain, hostile)
            matches = [row for row in rows if row.get("Source") == displayed(edge["source"])
                       and row.get("Scenario ID") == displayed(edge["scenario_id"])]
            self.assertEqual(len(matches), 1)
            row = matches[0]
            for label, field in (("Scenario ID", "scenario_id"), ("Cwd", "cwd"),
                                 ("Target", "target_text"), ("Condition", "condition")):
                self.assertEqual(row[label], displayed(edge[field]))
            self.assertEqual(row["Classification"], "read_dependency")
            self.assertEqual({part.strip().strip("`") for part in row["Base alternatives"].split("<br>")},
                             {displayed(value) for value in edge["alternatives"]})
            directory = next(row for row in rows if "Directory" in row
                             and row["Scenario ID"] == displayed(chain["scenario_id"]))
            self.assertEqual(directory["Cwd"], displayed(chain["cwd"]))
            self.assertEqual(directory["Directory"], displayed(str(self.root / "docs") + hostile))
        self.assertEqual(report, before)

    def test_existing_coverage_unassessed_and_route_cap_disclosures_remain_visible(self):
        self.source_text("No linked references.\n")
        report = self.report(self.scenarios())
        self.assertIn("Coverage: declared area complete.", render_audit(report))
        report.update(partial=True, route_limit_reached=True)
        rendered = render_audit(report)
        self.assertIn("Coverage: partial.", rendered)
        self.assertIn("Route stream truncated by --max-routes; coverage is partial.", rendered)
        self.assertIn("Semantic assessment: unassessed. No semantic PASS is implied.", rendered)


if __name__ == "__main__":
    unittest.main()
