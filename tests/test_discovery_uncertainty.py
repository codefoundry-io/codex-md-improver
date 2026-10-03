"""Required unknown facts and scanner frontiers stay distinct from loader errors."""
from pathlib import Path
import unittest
from unittest.mock import patch

import test_discovery as fixtures
from discovery import resolve_settings, scan


class UncertaintyTests(unittest.TestCase):
    setUp = fixtures.DiscoveryTests.setUp
    put = fixtures.DiscoveryTests.put
    trust = fixtures.DiscoveryTests.trust
    request = fixtures.DiscoveryTests.request

    def test_invalid_git_metadata_encoding_retains_report(self):
        child = self.root / "child"
        self.put(child / ".git", b"gitdir: \xff\n")
        self.put(child / "AGENTS.md", "child")
        try:
            report = scan(self.request())
        except UnicodeError as error:
            self.fail("A malformed Git pointer escaped scan: " + str(error))
        self.assertEqual(report["exit_code"], 3)
        self.assertTrue(any(f["path"] == str(child / ".git") and f["kind"] == "blocked"
                            for f in report["frontiers"]))
        self.assertIn(str(self.root), [r["cwd"] for r in report["chains"]])

    def test_missing_cwd_trust_fact_cannot_be_replaced_by_root_fallback(self):
        child = self.root / "child"
        self.put(child / "AGENTS.md", "child")
        settings = {"trust": {str(self.root): "trusted"},
                    "non_project": {"limit": 100, "fallback_names": [], "root_markers": [".git"]}}
        self.put(self.home / "config.toml", "projects=[]\n")
        request = self.request(settings, child)
        self.assertEqual(resolve_settings(request, child).trust, "unknown")
        report = scan(request)
        self.assertIsNone(report["chains"][0]["project_included_bytes"])
        self.assertEqual(report["exit_code"], 3)
        settings["trust"][str(child)] = "trusted"
        self.assertEqual(resolve_settings(self.request(settings, child), child).trust, "trusted")

    def test_unknown_group_discovery_is_not_known_loader_failure(self):
        group = {"id": "unknown", "cwds": [str(self.root)],
                 "effective_loader_settings": {"limit": 100, "trust": "trusted"}}
        report = scan(self.request({"environment_groups": [group]}, self.root))
        member = report["groups"][0]["members"][0]
        self.assertIsNone(member["project_included_bytes"])
        self.assertIsNone(member["modeled_loader_error"])
        self.assertEqual(report["groups"][0]["possible_outcomes"], ["unresolved"])
        self.assertEqual(report["exit_code"], 3)

    def test_denied_shadowed_variant_preserves_partial_scope(self):
        bad = self.root / "AGENTS.md"
        self.put(self.root / "AGENTS.override.md", "healthy")
        original = Path.read_bytes
        def read(path):
            if path == bad:
                raise PermissionError("shadowed scope analysis source")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            report = scan(self.request(cwd=self.root))
        self.assertEqual(report["chains"][0]["project_included_bytes"], 7)
        self.assertTrue(report["chains"][0]["partial"])
        self.assertEqual(report["exit_code"], 3)


if __name__ == "__main__":
    unittest.main()
