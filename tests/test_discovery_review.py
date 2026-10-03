"""Regression cases for independent Task 1 source-review findings."""
from pathlib import Path
import unittest
from unittest.mock import patch

import test_discovery as fixtures
import discovery
from discovery import resolve_settings, scan


class DiscoveryReviewTests(unittest.TestCase):
    setUp = fixtures.DiscoveryTests.setUp
    put = fixtures.DiscoveryTests.put
    trust = fixtures.DiscoveryTests.trust
    request = fixtures.DiscoveryTests.request
    chain = fixtures.DiscoveryTests.chain

    def group(self, roots, **effective):
        return {"id": "review", "cwds": [str(p) for p in roots],
                "effective_loader_settings": {"limit": 100, "fallback_names": [],
                    "root_markers": [], "trust": "trusted", **effective}}

    def test_child_metadata_denial_preserves_later_sibling(self):
        denied = self.root / "a-denied"
        denied.mkdir()
        healthy = self.root / "z-healthy"
        self.put(healthy / "AGENTS.md", "healthy")
        original = Path.is_dir
        def is_dir(path):
            if path == denied:
                raise PermissionError("synthetic child denial")
            return original(path)
        with patch.object(Path, "is_dir", is_dir):
            report = scan(self.request())
        self.assertIn(str(healthy), [r["cwd"] for r in report["chains"]])
        self.assertTrue(any(f["path"] == str(denied) and f["kind"] == "blocked"
                            for f in report["frontiers"]))
        self.assertEqual(report["exit_code"], 3)

    def test_second_content_observation_failure_is_partial(self):
        bad = self.root / "AGENTS.md"
        healthy = self.base / "healthy"
        self.put(healthy / "AGENTS.md", "healthy")
        original = discovery._Content.read
        observations = 0
        def read(content, path):
            nonlocal observations
            if path == bad:
                observations += 1
                if observations == 2:
                    raise OSError("file changed during scan")
            return original(content, path)
        with patch.object(discovery._Content, "read", read):
            try:
                report = scan(self.request(projects=[self.root, healthy]))
            except OSError as error:
                self.fail("An isolated second-read failure escaped scan: " + str(error))
        rows = {r["cwd"]: r for r in report["chains"]}
        self.assertEqual(rows[str(healthy)]["project_included_bytes"], 7)
        self.assertEqual(rows[str(self.root)]["loader_outcome"], "environment_read_error")
        self.assertEqual(report["exit_code"], 3)

    def test_session_markers_control_project_config_ancestry(self):
        self.trust()
        self.put(self.root / ".codex/config.toml", "project_doc_max_bytes=5\n")
        child = self.root / "child"
        self.put(child / "AGENTS.md", "0123456789")
        row = self.chain(child, {"session_overrides": {"root_markers": []}})
        self.assertEqual(row["scenario_project_root"], str(child))
        self.assertEqual(row["settings"]["limit"], 32768)
        self.assertEqual(row["project_included_bytes"], 10)

    def test_invalid_required_trust_shapes_are_unknown(self):
        for text in ("projects=[]\n", '[projects]\n"' + str(self.root) + '"="trusted"\n'):
            with self.subTest(text=text):
                self.put(self.home / "config.toml", text)
                request = self.request(cwd=self.root)
                self.assertEqual(resolve_settings(request, self.root).trust, "unknown")
                report = scan(request)
                self.assertIsNone(report["chains"][0]["project_included_bytes"])
                self.assertEqual(report["exit_code"], 3)

    def test_scanner_failure_after_gate_is_not_loader_failure(self):
        other = self.base / "other"
        bad = self.put(other / "AGENTS.md", "bad")
        original = Path.stat
        def metadata(path, *args, **kwargs):
            if path == bad:
                raise PermissionError("scanner metadata denial")
            return original(path, *args, **kwargs)
        for effective in ({"limit": 17}, {"trust": "untrusted"}, {"limit": 0}):
            with self.subTest(effective=effective):
                group = self.group([self.root, other], **effective)
                with patch.object(Path, "stat", metadata):
                    report = scan(self.request({"environment_groups": [group]}, projects=[self.root, other]))
                self.assertEqual(report["groups"][0]["members"][1]["project_included_bytes"], 0)
                self.assertNotIn("propagated_failure", report["groups"][0]["possible_outcomes"])
                self.assertEqual(report["exit_code"], 3)

    def test_group_only_warning_sets_finding_exit(self):
        self.put(self.root / "AGENTS.md", "x" * 10000)
        group = self.group([self.root], limit=8000)
        report = scan(self.request({"environment_groups": [group]}, cwd=self.root))
        self.assertFalse(report["chains"][0]["warning"])
        self.assertEqual(report["groups"][0]["members"][0]["project_included_bytes"], 8000)
        self.assertEqual(report["exit_code"], 1)

    def test_git_pointer_ascii_whitespace_variants(self):
        self.trust()
        linked = self.base / "linked"
        admin = self.root / ".git/worktrees/linked"
        self.put(admin / "gitdir", str(linked / ".git") + "\n")
        self.put(admin / "commondir", "../..\n")
        for space in ("", "\t", "   "):
            with self.subTest(space=space):
                self.put(linked / ".git", "gitdir:" + space + str(admin) + "\n")
                self.assertEqual(resolve_settings(self.request(projects=[linked]), linked).trust, "trusted")

    def test_unknown_group_remainder_is_not_reset(self):
        other = self.base / "other"
        self.put(other / "AGENTS.md", "healthy")
        bad = self.root / "AGENTS.md"
        original = Path.read_bytes
        def read(path):
            if path == bad:
                raise PermissionError("earlier group member")
            return original(path)
        group = self.group([self.root, other])
        with patch.object(Path, "read_bytes", read):
            report = scan(self.request({"environment_groups": [group]}, projects=[self.root, other]))
        self.assertIsNone(report["groups"][0]["members"][1]["project_included_bytes"])

    def test_ignored_fallback_names_keep_reasons(self):
        names = ["", ".", "..", "docs/X.md", "A.md", "A.md", "AGENTS.md"]
        settings = resolve_settings(self.request({"non_project": {"fallback_names": names}}), self.root)
        self.assertEqual(settings.fallback_names, ["A.md"])
        ignored = settings.provenance.get("ignored_fallback_names", [])
        self.assertEqual([v["value"] for v in ignored], ["", ".", "..", "docs/X.md", "A.md", "AGENTS.md"])
        self.assertTrue(all(v["reason"] for v in ignored))

    def test_source_aliases_expose_physical_identity(self):
        self.put(self.home / "AGENTS.md", "global")
        row = self.chain()
        for source in (row["sources"][0], row["global_source"], row["scope_sources"][0]):
            info = Path(source["path"]).stat()
            self.assertEqual(source.get("physical_identity"), [info.st_dev, info.st_ino])

    def test_identified_git_storage_is_not_a_cwd(self):
        admin = self.root / "storage"
        self.put(admin / "HEAD", "ref: refs/heads/main\n")
        linked = self.root / "linked"
        self.put(linked / ".git", "gitdir: " + str(admin) + "\n")
        self.put(admin / "objects/AGENTS.md", "administrative content")
        report = scan(self.request())
        self.assertFalse(any(Path(r["cwd"]).is_relative_to(admin) for r in report["chains"]))
        self.assertTrue(any(f["path"] == str(admin) and f["kind"] == "git_administration"
                            for f in report["frontiers"]))
        self.assertFalse(report["partial"])


if __name__ == "__main__":
    unittest.main()
