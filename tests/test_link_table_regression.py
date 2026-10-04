"""Portable synthetic graph tests; candidate source is imported only by executor."""
import copy
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

SOT = Path(__file__).resolve().parents[1] / "skills/codex-md-improver"
sys.path.insert(0, str(SOT / "scripts"))
from references import build_reference_graph, iter_terminal_paths, summarize_reading_paths


# Neutral nine-row counterpart of the private reproduction; no host layout.
OPERATION_ROWS = tuple((f"Operation {index}", f"policy-{index}.md") for index in range(1, 10))
OPERATION_EXCERPT = (
    "- Follow `docs/policies/common.md` for working rules and approval boundaries.\n"
    "\n## Load for the current operation\n\n"
    "| Operation | Reference |\n|---|---|\n"
    + "".join(f"| {operation} | `docs/policies/{name}` |\n"
              for operation, name in OPERATION_ROWS)
)


class LinkTableRegressionTests(unittest.TestCase):
    def setUp(self):
        scratch = os.environ.get("CODEX_MD_TEST_TMP")
        self.temp = tempfile.TemporaryDirectory(prefix="link-table-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "project"
        self.home = self.base / "home"
        self.root.mkdir()
        self.home.mkdir()
        self.source = self.root / "AGENTS.md"

    def put(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def chain(self, cwd=None, scenario="one"):
        data = self.source.read_bytes()
        return {"scenario_id": scenario, "cwd": str(cwd or self.root),
                "scenario_project_root": str(self.root), "inventory_root": str(self.root),
                "sources": [{"path": str(self.source),
                             "sha256": hashlib.sha256(data).hexdigest(), "original_bytes": len(data)}],
                "scope_sources": [], "global_source": {"path": None, "original_bytes": 0},
                "project_original_bytes": len(data), "project_included_bytes": len(data)}

    def build(self, chains=None, bases=None, resolutions=None):
        self.chains = chains or [self.chain()]
        return build_reference_graph(self.chains, bases or {}, resolutions or [],
                                     context={"codex_home": self.home, "user_home": self.home})

    def routes(self, graph):
        return [row for chain in self.chains for row in iter_terminal_paths(graph, chain)]

    def exact_decision(self, target):
        text = self.source.read_text(encoding="utf-8")
        start = text.index(target)
        return {"source": str(self.source),
                "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                "span": [start, start + len(target)], "text": target,
                "classification": "read_dependency", "base": {"kind": "document_dir"}}

    def test_operation_table_reads_all_nine_and_counts_unique_bytes(self):
        self.put("AGENTS.md", OPERATION_EXCERPT)
        expected = {str(self.put("docs/policies/common.md", "common\n")): 7}
        row_conditions = {}
        for index, (operation, name) in enumerate(OPERATION_ROWS):
            content = "정책" + ("x" * (index + 1)) + "\n"
            path = self.put("docs/policies/" + name, content)
            expected[str(path)] = len(content.encode("utf-8"))
            row_conditions["docs/policies/" + name] = f"| {operation} | `docs/policies/{name}` |"
        chains = [self.chain(scenario="one"), self.chain(scenario="two")]
        before = copy.deepcopy(chains)
        graph = self.build(chains)
        self.assertEqual(chains, before, "Reference traversal must preserve loader selection and L")
        table_edges = [edge for edge in graph["occurrences"] if edge["target_text"] in row_conditions]
        self.assertEqual(len(table_edges), 18)
        for edge in table_edges:
            self.assertEqual(edge["classification"], "read_dependency")
            self.assertEqual(edge["status"], "resolved")
            self.assertEqual(edge["condition"], row_conditions[edge["target_text"]])
        routes = self.routes(graph)
        self.assertEqual(len(routes), 20)
        loader_bytes = len(OPERATION_EXCERPT.encode("utf-8"))
        for scenario in ("one", "two"):
            rows = [row for row in routes if row["scenario_id"] == scenario]
            self.assertEqual({row["terminal_path"] for row in rows}, set(expected))
            for row in rows:
                size = expected[row["terminal_path"]]
                self.assertEqual(row["terminal_kind"], "leaf")
                self.assertEqual(row["reference_original_bytes"], size)
                self.assertEqual(row["route_original_bytes"], loader_bytes + size)
                self.assertEqual(row["project_included_bytes"], loader_bytes)
                self.assertTrue(row["conditions"])
                self.assertFalse(row["lower_bound"])
        summary = summarize_reading_paths(graph)
        self.assertEqual(summary["unique_text_bytes"], loader_bytes + sum(expected.values()))
        self.assertEqual(summary["physical_text_files"], 11)
        self.assertFalse(summary["partial"])

    def test_minimal_common_seven_environment_twelve_adds_nineteen_to_L(self):
        loader = ("Follow `common.md`.\n\n## Load for the current operation\n\n"
                  "| Operation | Reference |\n|---|---|\n| Build | `environment.md` |\n")
        self.put("AGENTS.md", loader)
        common = self.put("common.md", "common\n")
        environment = self.put("environment.md", "environment\n")
        chain = self.chain()
        before = copy.deepcopy(chain)
        graph = self.build([chain])
        loader_bytes = len(loader.encode("utf-8"))
        self.assertEqual(summarize_reading_paths(graph)["unique_text_bytes"], loader_bytes + 19)
        self.assertEqual({row["terminal_path"]: row["reference_original_bytes"] for row in self.routes(graph)},
                         {str(common): 7, str(environment): 12})
        self.assertEqual(chain, before)
        self.assertEqual(chain["project_included_bytes"], loader_bytes)

    def test_explicit_Read_column_is_an_existing_read_dependency_control(self):
        self.put("AGENTS.md", "| Operation | Read |\n|---|---|\n| Build | `guide.md` |\n")
        target = self.put("guide.md", "control\n")
        graph = self.build()
        self.assertEqual([(e["classification"], e["status"]) for e in graph["occurrences"]],
                         [("read_dependency", "resolved")])
        self.assertEqual([row["terminal_path"] for row in self.routes(graph)], [str(target)])
        self.assertFalse(graph["partial"])

    def test_exact_source_hash_span_text_resolution_control_and_stale_rejection(self):
        self.put("AGENTS.md", "| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n")
        target = self.put("guide.md", "resolved\n")
        decision = self.exact_decision("guide.md")
        graph = self.build(resolutions=[decision])
        self.assertEqual([row["terminal_path"] for row in self.routes(graph)], [str(target)])
        self.assertEqual(graph["occurrences"][0]["span"], decision["span"])
        self.assertEqual(graph["occurrences"][0]["source_sha256"], decision["source_sha256"])
        self.assertFalse(graph["partial"])
        for field, invalid in (("source_sha256", "0" * 64), ("span", [0, 8]), ("text", "wrong.md"),
                               ("source", str(self.root / "unselected.md"))):
            with self.subTest(field=field):
                stale = copy.deepcopy(decision)
                stale[field] = invalid
                with self.assertRaises(ValueError):
                    self.build(resolutions=[stale])

    def test_arbitrary_Reference_and_Bibliography_tables_remain_unresolved(self):
        for heading in ("Reference", "Bibliography"):
            with self.subTest(heading=heading):
                self.put("AGENTS.md", f"## {heading}\n\n| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n")
                self.put("guide.md", "not a declared read\n")
                graph = self.build()
                self.assertEqual([(e["classification"], e["status"]) for e in graph["occurrences"]],
                                 [("uncertain", "unresolved")])
                self.assertEqual([row["terminal_kind"] for row in self.routes(graph)], ["unresolved"])
                self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 1)

    def test_output_and_example_tables_do_not_inherit_Load_context(self):
        for label in ("Output", "Example"):
            with self.subTest(label=label):
                self.put("AGENTS.md", "## Load for the current operation\n\n"
                         f"| Operation | Reference |\n|---|---|\n| {label} | `result.md` |\n")
                self.put("result.md", "must not enter graph\n")
                graph = self.build()
                self.assertNotEqual(graph["occurrences"][0]["classification"], "read_dependency")
                self.assertEqual(graph["occurrences"][0]["targets"], [])
                self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 1)

    def test_later_heading_ends_operation_Load_context(self):
        self.put("AGENTS.md", "## Load for the current operation\n\nIntroductory text.\n\n"
                 "## Catalog\n\n| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n")
        self.put("guide.md", "catalog only\n")
        graph = self.build()
        self.assertEqual([(e["classification"], e["status"]) for e in graph["occurrences"]],
                         [("uncertain", "unresolved")])
        self.assertEqual([row["terminal_kind"] for row in self.routes(graph)], ["unresolved"])
        self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 1)

    def test_nested_cwd_base_ambiguity_survives_read_table_classification(self):
        self.put("AGENTS.md", "## Load for the current operation\n\n"
                 "| Operation | Reference |\n|---|---|\n| Build | `docs/guide.md` |\n")
        target = self.put("docs/guide.md", "one existing candidate\n")
        cwd = self.root / "nested"
        cwd.mkdir()
        graph = self.build([self.chain(cwd=cwd)])
        edge = graph["occurrences"][0]
        self.assertEqual(edge["classification"], "read_dependency")
        self.assertEqual(edge["status"], "unresolved")
        self.assertEqual(set(edge["alternatives"]), {str(target), str(cwd / "docs/guide.md")})
        self.assertEqual(edge["targets"], [])
        self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 1)
        resolved = self.build([self.chain(cwd=cwd)], bases={str(self.source): {"kind": "document_dir"}})
        self.assertEqual([row["terminal_path"] for row in self.routes(resolved)], [str(target)])
        self.assertFalse(resolved["partial"])


if __name__ == "__main__":
    unittest.main()
