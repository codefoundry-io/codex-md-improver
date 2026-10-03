"""Selected Git administration roots remain explicit inventory boundaries."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tests"))
sys.path.insert(0, str(PROJECT / "skills/codex-md-improver/scripts"))
import test_references as fixtures
from discovery import ScopeRequest, _Content, scan


class SelectedGitAdministrationRoots(unittest.TestCase):
    # Helpers only, with CODEX_MD_TEST_TMP and automatic fixture cleanup.
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def request(self, projects, cwd=None):
        return ScopeRequest(projects, self.home, cwd, {
            "non_project": {"limit": 32768, "root_markers": [".git"],
                            "fallback_names": []},
            "trust": {str(self.root): "trusted"}})

    def administration(self):
        admin = self.root / ".git"
        self.put(admin / "HEAD", "ref: refs/heads/main\n")
        self.put(admin / "AGENTS.md", "administrative root instructions\n")
        nested = admin / "objects/nested"
        self.put(nested / "AGENTS.md", "administrative descendant instructions\n")
        return admin, nested

    def tracked_scan(self, request):
        reads = []
        original = _Content.read
        def track(content, path):
            reads.append(Path(path))
            return original(content, path)
        with patch.object(_Content, "read", track):
            report = scan(request)
        return report, reads

    def assert_excluded(self, report, reads, selected, admin, expected_exit):
        self.assertEqual(report["chains"], [])
        self.assertFalse(report["partial"])
        self.assertTrue(report["inventory_complete"])
        self.assertEqual(report["exit_code"], expected_exit)
        # Permit either the whole administration boundary or the excluded
        # selected subtree; require the visible frontier to cover the input.
        self.assertTrue(any(
            row["kind"] == "git_administration"
            and selected.resolve().is_relative_to(Path(row["path"]).resolve())
            for row in report["frontiers"]))
        self.assertFalse(any(path.resolve().is_relative_to(admin) for path in reads))
        self.assertNotIn(self.source, reads,
                         "An excluded cwd must not load parent project guidance")

    def test_exact_git_root_without_global_has_no_usable_input(self):
        admin, _ = self.administration()
        report, reads = self.tracked_scan(self.request([admin]))
        # Exit 2 follows absent usable input, not partial reference coverage.
        self.assert_excluded(report, reads, admin, admin, expected_exit=2)

    def test_descendant_git_root_with_global_is_excluded_in_both_inventory_modes(self):
        admin, nested = self.administration()
        global_source = self.put(self.home / "AGENTS.md", "global guidance\n")
        for cwd in (None, nested):
            with self.subTest(cwd=cwd):
                report, reads = self.tracked_scan(self.request([nested], cwd))
                self.assert_excluded(report, reads, nested, admin, expected_exit=0)
                self.assertIn(global_source, reads)

    def test_selected_alias_into_git_is_a_physical_boundary(self):
        admin, nested = self.administration()
        alias = self.base / "selected-alias"
        alias.symlink_to(nested, target_is_directory=True)
        self.put(self.home / "AGENTS.md", "global guidance\n")
        report, reads = self.tracked_scan(self.request([alias]))
        self.assert_excluded(report, reads, alias, admin, expected_exit=0)

    def test_ordinary_project_git_presence_is_complete_control(self):
        admin, _ = self.administration()
        report, reads = self.tracked_scan(self.request([self.root]))
        self.assertEqual([row["cwd"] for row in report["chains"]], [str(self.root)])
        self.assertFalse(report["partial"])
        self.assertTrue(report["inventory_complete"])
        self.assertEqual(report["exit_code"], 0)
        self.assertIn({"path": str(admin), "kind": "git_administration"},
                      report["frontiers"])
        self.assertIn(self.source, reads)
        self.assertFalse(any(path.resolve().is_relative_to(admin) for path in reads))

    def test_cross_selected_ordinary_directory_alias_remains_in_scope_control(self):
        self.administration()
        outside = self.base / "ordinary-second-project"
        ordinary = self.put(outside / "AGENTS.md", "ordinary selected guidance\n")
        alias = self.root / "ordinary-alias"
        alias.symlink_to(outside, target_is_directory=True)
        report, reads = self.tracked_scan(self.request([self.root, outside]))
        self.assertEqual({row["cwd"] for row in report["chains"]},
                         {str(self.root), str(alias), str(outside)})
        self.assertFalse(report["partial"])
        self.assertTrue(report["inventory_complete"])
        self.assertEqual(report["exit_code"], 0)
        self.assertTrue(any(path.resolve() == ordinary for path in reads))


if __name__ == "__main__":
    unittest.main()
