"""Remaining route-context and group-only input regressions."""
import json
import os
import unittest
import test_references as fixtures


class FinalReferenceTests(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    cli = fixtures.ReferenceTests.cli

    def test_cached_intermediate_revisits_cycle_alias_in_new_route(self):
        self.put(self.source, "[a](a.md)\n[b](b.md)\n")
        a = self.put(self.root / "a.md", "[b](b.md)\n")
        b = self.put(self.root / "b.md", "[alias](alias-a.md)\n")
        alias = self.root / "alias-a.md"
        os.link(a, alias)
        graph = self.build()
        rows = self.routes(graph)
        direct_b = next(row for row in rows if row["route"][1] == str(b))
        self.assertEqual(direct_b["route"], [str(self.source), str(b), str(alias), str(b)])
        self.assertEqual(direct_b["terminal_kind"], "cycle")

    def test_group_only_readable_source_is_usable(self):
        self.source.unlink()
        self.put(self.root / "ALT.md", "group-only guidance")
        group = {"id": "only", "cwds": [str(self.root)],
                 "effective_loader_settings": {"limit": 100, "fallback_names": ["ALT.md"],
                                               "root_markers": [], "trust": "trusted"}}
        settings = self.put(self.base / "settings.json", json.dumps({"environment_groups": [group]}))
        proc, out = self.cli(["--settings", str(settings)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads((out / "audit.json").read_text())
        self.assertFalse(report["partial"])
        self.assertEqual(report["groups"][0]["project_included_bytes"], 19)


if __name__ == "__main__":
    unittest.main()
