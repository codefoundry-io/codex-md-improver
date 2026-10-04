"""Bounded heading/column controls supplementing the preserved first RED."""
import unittest
import test_link_table_regression as fixtures
from references import summarize_reading_paths


class LinkTableBounds(unittest.TestCase):
    setUp = fixtures.LinkTableRegressionTests.setUp
    put = fixtures.LinkTableRegressionTests.put
    chain = fixtures.LinkTableRegressionTests.chain
    build = fixtures.LinkTableRegressionTests.build
    routes = fixtures.LinkTableRegressionTests.routes

    def test_See_also_and_Follow_up_tasks_do_not_declare_read_tables(self):
        for heading in ("See also", "Follow-up tasks"):
            with self.subTest(heading=heading):
                self.put("AGENTS.md", f"## {heading}\n\n| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n")
                self.put("guide.md", "not declared\n")
                graph = self.build()
                self.assertEqual([(e["classification"], e["status"]) for e in graph["occurrences"]],
                                 [("uncertain", "unresolved")])
                self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 1)

    def test_fenced_Load_heading_does_not_leak_into_real_table(self):
        self.put("AGENTS.md", "```markdown\n## Load for the current operation\n```\n\n"
                 "| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n")
        self.put("guide.md", "outside fence\n")
        graph = self.build()
        self.assertEqual([(e["classification"], e["status"]) for e in graph["occurrences"]],
                         [("uncertain", "unresolved")])
        self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 1)

    def test_Load_context_traverses_only_Reference_column(self):
        self.put("AGENTS.md", "## Load for the current operation\n\n"
                 "| Operation | Reference |\n|---|---|\n| `operation/` | `guide.md` |\n")
        target = self.put("guide.md", "declared read\n")
        self.put("operation/uncounted.md", "not an instruction reference\n")
        graph = self.build()
        edges = {e["target_text"]: e for e in graph["occurrences"]}
        self.assertEqual(edges["guide.md"]["classification"], "read_dependency")
        self.assertEqual(edges["guide.md"]["targets"], [str(target)])
        self.assertEqual(edges["operation/"]["classification"], "uncertain")
        self.assertEqual(edges["operation/"]["targets"], [])
        self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 2)
        self.assertEqual(graph["directory_summaries"], {})

    def test_Setext_Load_is_positive_and_later_Setext_Catalog_ends_context(self):
        self.put("AGENTS.md", "Load for the current operation\n------------------------------\n\n"
                 "| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n\n"
                 "Catalog\n-------\n\n| Operation | Reference |\n|---|---|\n| Build | `catalog.md` |\n")
        target = self.put("guide.md", "declared read\n")
        self.put("catalog.md", "catalog only\n")
        graph = self.build()
        edges = {e["target_text"]: e for e in graph["occurrences"]}
        self.assertEqual(edges["guide.md"]["classification"], "read_dependency")
        self.assertEqual(edges["guide.md"]["targets"], [str(target)])
        self.assertEqual(edges["catalog.md"]["classification"], "uncertain")
        self.assertEqual(edges["catalog.md"]["status"], "unresolved")
        self.assertEqual(summarize_reading_paths(graph)["physical_text_files"], 2)


if __name__ == "__main__":
    unittest.main()
