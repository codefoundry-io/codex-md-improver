"""Behavioral regression: forbidden bodies never reach the byte-read boundary."""
import builtins
import io
from contextlib import ExitStack, contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_references as fixtures
from discovery import ScopeRequest, scan, _Content
from md_improver import main
from reporting import compare_reports, enrich_audit, report_hash


class MetadataOnlyTests(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def settings(self, paths):
        return {"schema_version": 1, "metadata_only_paths": [str(p) for p in paths],
                "non_project": {"limit": 32768, "root_markers": [".git"], "fallback_names": []},
                "trust": {str(self.root): "trusted"}}

    def run_scan(self, paths, *, cwd=False):
        settings = self.put(self.base / "settings.json", json.dumps(self.settings(paths)))
        out = self.base / ("out-" + str(len(list(self.base.glob("out-*")))))
        argv = ["scan", "--project", str(self.root), "--codex-home", str(self.home),
                "--settings", str(settings), "--out", str(out)]
        if cwd:
            argv += ["--cwd", str(self.root)]
        status = main(argv)
        audit = json.loads((out / "audit.json").read_bytes()) if (out / "audit.json").exists() else None
        return status, audit, out

    @contextmanager
    def guard(self, target):
        identity = (target.stat().st_dev, target.stat().st_ino)
        def check(path):
            try:
                info = os.fstat(path) if isinstance(path, int) else Path(path).stat()
            except (OSError, TypeError):
                return
            if (info.st_dev, info.st_ino) == identity:
                raise AssertionError("Forbidden body reached byte-read boundary")
        def wrap(original):
            def guarded(path, *args, **kwargs):
                check(path)
                return original(path, *args, **kwargs)
            return guarded
        with ExitStack() as stack:
            for owner, name in ((Path, "read_bytes"), (io, "open"),
                                (builtins, "open"), (os, "open")):
                stack.enter_context(patch.object(owner, name, wrap(getattr(owner, name))))
            yield

    def test_guard_control_rejects_alias_and_allows_independent_file(self):
        protected = self.put(self.root / "protected.md", "secret")
        alias = self.root / "alias.md"
        os.link(protected, alias)
        allowed = self.put(self.root / "allowed.md", "okay")
        with self.guard(protected):
            with self.assertRaises(AssertionError):
                alias.read_bytes()
            self.assertEqual(allowed.read_bytes(), b"okay")

    def test_recursive_scan_excludes_all_alias_routes_but_reads_sibling(self):
        protected = self.put(self.root / "docs/hold.md", "PROTECTED_BODY")
        self.put(self.root / "docs/okay.md", "allowed body")
        os.link(protected, self.root / "docs/hard.md")
        (self.root / "docs/link.md").symlink_to(protected)
        self.put(self.source, "[direct](docs/hold.md)\n[tree](docs/)\n[glob](docs/*.md)\n")
        with self.guard(protected):
            code, audit, out = self.run_scan([protected])
        self.assertEqual(code, 3)
        self.assertIsNotNone(audit)
        self.assertTrue(audit["partial"])
        self.assertFalse(audit["text_read_complete"])
        nodes = audit["graph"]["nodes"].values()
        self.assertIn(str(self.root / "docs/okay.md"), {a for n in nodes for a in n["aliases"]})
        forbidden = {str(self.root / "docs" / p) for p in ("hold.md", "hard.md", "link.md")}
        self.assertFalse(forbidden & {a for n in nodes for a in n["aliases"]})
        states = [s for s in audit["graph"]["states"].values() if s["path"] in forbidden]
        self.assertEqual({s["kind"] for s in states}, {"excluded_metadata_only"})
        self.assertEqual({s["metadata_bytes"] for s in states}, {14})
        self.assertTrue(all(s["bytes"] is None for s in states))
        self.assertNotIn("PROTECTED_BODY", (out / "audit.json").read_text())
        self.assertIn("Metadata-only", (out / "audit.md").read_text())
        summaries = [values[str(self.root / "docs")] for values in
                     audit["reading_summary"]["directory_summaries_by_scenario"].values()
                     if str(self.root / "docs") in values]
        self.assertTrue(summaries)
        self.assertTrue(all(row["lower_bound"] for row in summaries))
        self.assertTrue(all(row["frontier_counts"].get("excluded_metadata_only", 0) > 0
                            for row in summaries))
        routes = [json.loads(line) for line in (out / "routes.jsonl").read_text().splitlines()]
        excluded = [row for row in routes if row["terminal_kind"] == "excluded_metadata_only"]
        self.assertTrue(excluded)
        self.assertTrue(all(row["lower_bound"] and row["terminal_bytes"] is None for row in excluded))
        self.assertIn("excluded_metadata_only", (out / "audit.md").read_text())

    def test_selected_project_guidance_is_unknown_without_fallback_body(self):
        self.put(self.root / "AGENTS.override.md", "OVERRIDE")
        with self.guard(self.root / "AGENTS.override.md"):
            code, audit, _ = self.run_scan([self.root / "AGENTS.override.md"], cwd=True)
        self.assertEqual(code, 3)
        chain = audit["chains"][0]
        self.assertIsNone(chain["project_original_bytes"])
        self.assertIsNone(chain["project_included_bytes"])
        self.assertEqual(chain["loader_outcome"], "unresolved")
        self.assertIsNone(chain["modeled_loader_error"])
        row = chain["sources"][0]
        self.assertEqual(row["metadata_bytes"], 8)
        self.assertIsNone(row["sha256"])
        self.assertEqual(row["read_error"], "MetadataOnlyError")

    def test_global_override_denial_does_not_select_fallback(self):
        target = self.put(self.home / "AGENTS.override.md", "OVERRIDE")
        self.put(self.home / "AGENTS.md", "global fallback")
        with self.guard(target):
            code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        global_source = audit["chains"][0]["global_source"]
        self.assertEqual(global_source["path"], str(target))
        self.assertEqual(global_source["state"], "metadata_only")
        self.assertIsNone(global_source["included_bytes"])
        self.assertIsNone(global_source["original_bytes"])
        self.assertEqual(global_source["metadata_bytes"], 8)
        self.assertEqual(global_source["warnings"][0]["error"], "MetadataOnlyError")

    def test_unselected_variant_has_metadata_without_hash(self):
        target = self.put(self.source, "denied")
        self.put(self.root / "AGENTS.override.md", "permitted override")
        with self.guard(target):
            code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        rows = [s for s in audit["chains"][0]["scope_sources"] if s["path"] == str(target)]
        self.assertEqual(rows[0]["metadata_bytes"], 6)
        self.assertIsNone(rows[0]["sha256"])

    def test_config_denial_is_unresolved_and_body_never_read(self):
        target = self.put(self.home / "config.toml", "project_doc_max_bytes = 1")
        with self.guard(target):
            code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        self.assertTrue(audit["chains"][0]["settings"]["unresolved"])

    def test_missing_declaration_retains_reached_metadata_only_frontier(self):
        target = self.root / "missing.md"
        self.put(self.source, "[missing](missing.md)")
        code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        rows = [s for s in audit["graph"]["states"].values() if s["path"] == str(target)]
        self.assertEqual(rows[0]["kind"], "excluded_metadata_only")
        self.assertIsNone(rows[0]["metadata_bytes"])

    def test_invalid_declarations_fail_before_output_creation(self):
        for value in ("not-a-list", ["relative.md"], [str(self.root)], [str(self.root / "*.md")], [str(self.root / "../other")], [42]):
            with self.subTest(value=value):
                settings = self.settings([])
                settings["metadata_only_paths"] = value
                with self.assertRaises(ValueError):
                    scan(ScopeRequest([self.root], self.home, self.root, settings))

    def test_standalone_graph_honors_metadata_context(self):
        target = self.put(self.root / "hold.md", "SECRET")
        self.put(self.source, "[target](hold.md)")
        chains = [fixtures.ReferenceTests.chain(self)]
        with self.guard(target):
            graph = fixtures.build_reference_graph(chains, context={"metadata_only_paths": [str(target)],
                                                                  "codex_home": self.home})
        self.assertTrue(graph["partial"])
        self.assertTrue(any(s["kind"] == "excluded_metadata_only" for s in graph["states"].values()))

    def test_report_refuses_forged_readable_alias_of_denied_file(self):
        target = self.put(self.root / "hold.md", "secret")
        alias = self.root / "alias.md"
        os.link(target, alias)
        self.put(self.source, "[target](hold.md)")
        code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        digest = hashlib.sha256(b"secret").hexdigest()
        audit["graph"]["nodes"]["forged"] = {"aliases": [str(alias)], "sha256": digest,
                                              "content_status": "read", "bytes": 6}
        assessment = {"schema_version": 1, "audit_sha256": report_hash(audit),
                      "reviewed_sources": [{"source": str(alias), "source_sha256": digest}]}
        with self.guard(target), self.assertRaises(ValueError):
            enrich_audit(audit, assessment)

    def test_changed_boundary_is_not_comparable(self):
        _, audit, _ = self.run_scan([], cwd=True)
        self.assertIsNotNone(audit)
        after = copy.deepcopy(audit)
        after["scope"]["settings"]["metadata_only_paths"] = [str(self.root / "absent.md")]
        result = compare_reports(audit, after)
        self.assertFalse(result["comparable"])


if __name__ == "__main__":
    unittest.main()
