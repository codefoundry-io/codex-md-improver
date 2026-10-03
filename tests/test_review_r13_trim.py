"""R13 trust-only trim_ascii regressions for a dedicated executor.

VT remains a literal path character in pinned Rust trim_ascii semantics.
Inventory parsing deliberately retains its existing whitespace behavior.
"""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tests"))
sys.path.insert(0, str(PROJECT / "skills/codex-md-improver/scripts"))
import test_references as fixtures
import test_review_r12_trust as trust_fixtures
from discovery import _Content, _git_pointer, resolve_settings


class PinnedAsciiTrustTrim(unittest.TestCase):
    # Delegate helpers only; no inherited test methods. setUp honors
    # CODEX_MD_TEST_TMP and registers cleanup of its disposable fixture.
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    request = trust_fixtures.PinnedTrustPaths.request
    linked = trust_fixtures.PinnedTrustPaths.linked
    assert_unset = trust_fixtures.PinnedTrustPaths.assert_unset

    def assert_main_trusted(self, main):
        settings = resolve_settings(self.request(main), self.root)
        self.assertEqual((settings.trust, settings.trust_key),
                         ("trusted", str(main)))

    def test_trailing_vt_linked_pointer_does_not_use_trimmed_admin_decoy(self):
        main, _, admin = self.linked()
        self.assertTrue(admin.is_dir())
        self.assertFalse(Path(str(admin) + "\v").exists())
        self.put(self.root / ".git", "gitdir: " + str(admin) + "\v\n")
        self.assert_unset(self.request(main))

    def test_trailing_vt_backlink_does_not_use_trimmed_registration_decoy(self):
        main, _, admin = self.linked()
        registration = self.root / ".git"
        self.assertTrue(registration.is_file())
        self.assertFalse(Path(str(registration) + "\v").exists())
        self.put(admin / "gitdir", str(registration) + "\v\n")
        self.assert_unset(self.request(main))

    def test_trailing_vt_commondir_does_not_apply_project_settings(self):
        main, common, admin = self.linked()
        self.assertTrue(common.is_dir())
        self.assertFalse((admin / "../..\v").exists())
        self.put(admin / "commondir", "../..\v\n")
        self.put(self.root / ".codex/config.toml",
                 'project_doc_max_bytes = 7\n'
                 'project_doc_fallback_filenames = ["LOCAL.md"]\n')
        settings = self.assert_unset(self.request(main))
        self.assertEqual(settings.limit, 1000)
        self.assertEqual(settings.fallback_names, ["BASE.md"])

    def test_trailing_vt_main_pointer_does_not_use_trimmed_storage_decoy(self):
        main = self.base / "main"
        main, common, _ = self.linked(main, main / "storage")
        self.assertTrue(common.is_dir())
        self.assertFalse(Path(str(common) + "\v").exists())
        self.put(main / ".git", "gitdir: " + str(common) + "\v\n")
        self.assert_unset(self.request(main))

    def test_vt_before_gitdir_prefix_does_not_inherit_main_trust(self):
        main, _, admin = self.linked()
        self.put(self.root / ".git", "\vgitdir: " + str(admin) + "\n")
        self.assert_unset(self.request(main))

    def test_literal_vt_linked_admin_directory_inherits_main_trust(self):
        main, common, _ = self.linked()
        admin = common / "worktrees/linked\v"
        self.put(admin / "gitdir", str(self.root / ".git") + "\n")
        self.put(admin / "commondir", "../..\n")
        self.put(self.root / ".git", "gitdir: " + str(admin) + "\n")
        # Leave a broken ordinary admin decoy: trimming would select it, while
        # a blanket VT rejection would discard the valid literal admin.
        self.put(common / "worktrees/linked/gitdir", "invalid\n")
        self.assertTrue(admin.is_dir())
        self.assert_main_trusted(main)

    def test_literal_vt_common_storage_main_pointer_inherits_main_trust(self):
        main = self.base / "main"
        main, common, _ = self.linked(main, main / "storage\v")
        self.assertFalse((main / "storage").exists())
        self.put(main / ".git", "gitdir: " + str(common) + "\n")
        self.assert_main_trusted(main)

    def test_space_tab_lf_ff_cr_padding_still_inherits_main_trust(self):
        main = self.base / "main"
        main, common, admin = self.linked(main, main / "storage")
        padding = " \t\n\f\r"
        self.put(self.root / ".git",
                 padding + "gitdir:" + padding + str(admin) + padding)
        self.put(admin / "gitdir", padding + str(self.root / ".git") + padding)
        self.put(admin / "commondir", padding + "../.." + padding)
        self.put(main / ".git",
                 padding + "gitdir:" + padding + str(common) + padding)
        self.assert_main_trusted(main)

    def test_inventory_default_git_pointer_keeps_vt_trimming_control(self):
        _, _, admin = self.linked()
        self.put(self.root / ".git", "\vgitdir: \v" + str(admin) + "\v\n")
        self.assertEqual(_git_pointer(self.root / ".git", _Content()), admin)


if __name__ == "__main__":
    unittest.main()
