"""R12 trust regressions against pinned Codex PathUri semantics.

Git inventory retains filesystem semantics; these cases concern only loader
trust. Metadata path dot-dot is collapsed lexically before filesystem access.
"""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
from discovery import ScopeRequest, resolve_settings, scan


class PinnedTrustPaths(unittest.TestCase):
    # Delegate fixture helpers without inheriting unrelated test methods.
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def request(self, main, trust=None):
        # Only the main key is supplied: an exact cwd key would bypass fallback.
        return ScopeRequest([self.root], self.home, self.root, {
            'non_project': {'limit': 1000, 'root_markers': ['.git'],
                            'fallback_names': ['BASE.md']},
            'trust': trust if trust is not None else {str(main): 'trusted'}})

    def linked(self, main=None, common=None):
        main = main or self.base / 'main'
        common = common or main / '.git'
        admin = common / 'worktrees/linked'
        self.put(common / 'HEAD', 'ref: refs/heads/main\n')
        self.put(admin / 'gitdir', str(self.root / '.git') + '\n')
        self.put(admin / 'commondir', '../..\n')
        self.put(self.root / '.git', 'gitdir: ' + str(admin) + '\n')
        return main, common, admin

    def assert_unset(self, request):
        settings = resolve_settings(request, self.root)
        self.assertEqual(settings.trust, 'unset')
        self.assertIsNone(settings.trust_key)
        return settings

    def assert_readable_chain(self, request):
        # Malformed trust metadata is local; it must not erase readable input
        # or become the CLI's no-usable-input status. scan() exceptions fail.
        report = scan(request)
        self.assertNotEqual(report['exit_code'], 2)
        row = next(row for row in report['chains'] if row['cwd'] == str(self.root))
        self.assertEqual(row['settings']['trust'], 'unset')
        self.assertIsNone(row['settings']['trust_key'])
        self.assertTrue(any(source['path'] == str(self.source) and source['sha256']
                            for source in [*row['sources'], *row['scope_sources']]))

    def symlink_parent(self, absolute):
        main, _, admin = self.linked()
        child = admin.parent / 'child'
        child.mkdir()
        (self.root / 'bridge').symlink_to(child, target_is_directory=True)
        pointer = str(self.root / 'bridge/../linked') if absolute else 'bridge/../linked'
        self.assertEqual((self.root / pointer).resolve(strict=True), admin)
        self.assertFalse((self.root / 'linked').exists())
        self.put(self.root / '.git', 'gitdir: ' + pointer + '\n')
        self.assert_unset(self.request(main))

    def test_relative_symlink_parent_worktree_does_not_inherit_main_trust(self):
        self.symlink_parent(False)

    def test_absolute_symlink_parent_worktree_does_not_inherit_main_trust(self):
        self.symlink_parent(True)

    def test_main_checkout_pointer_uses_lexical_parent(self):
        main = self.base / 'main'
        main, common, _ = self.linked(main, main / 'storage')
        (common / 'child').mkdir()
        (main / 'alias').symlink_to('storage/child', target_is_directory=True)
        self.put(main / '.git', 'gitdir: alias/..\n')
        self.assertEqual((main / 'alias/..').resolve(strict=True), common)
        self.assert_unset(self.request(main))

    def test_missing_lexical_main_does_not_substitute_canonical_main(self):
        main, _, admin = self.linked(self.base / 'outer/realmain')
        child = self.base / 'outer/child'
        child.mkdir()
        (self.root / 'bridge').symlink_to(child, target_is_directory=True)
        pointer = self.root / 'bridge/../realmain/.git/worktrees/linked'
        self.assertEqual(pointer.resolve(strict=True), admin)
        self.assertFalse((self.root / 'realmain').exists())
        self.put(self.root / '.git', 'gitdir: ' + str(pointer) + '\n')
        self.assert_unset(self.request(main))

    def test_missing_component_collapses_before_filesystem_lookup_control(self):
        main, _, _ = self.linked()
        # The nonexistent component must not be stat-ed before lexical collapse.
        self.assertFalse((self.root / 'missing').exists())
        self.put(self.root / '.git', 'gitdir: missing/../../main/.git/worktrees/linked\n')
        settings = resolve_settings(self.request(main), self.root)
        self.assertEqual((settings.trust, settings.trust_key), ('trusted', str(main)))

    def test_normal_relative_linked_worktree_control(self):
        main, _, _ = self.linked()
        self.put(self.root / '.git', 'gitdir: ../main/.git/worktrees/linked\n')
        settings = resolve_settings(self.request(main), self.root)
        self.assertEqual((settings.trust, settings.trust_key), ('trusted', str(main)))

    def alias_settings(self, canonical_level=None):
        main, _, _ = self.linked(self.base / 'main-real')
        alias = self.base / 'main-alias'
        alias.symlink_to(main, target_is_directory=True)
        self.put(self.root / '.git', 'gitdir: ' + str(alias / '.git/worktrees/linked') + '\n')
        trust = {str(alias): 'trusted'}
        if canonical_level is not None:
            trust[str(main)] = canonical_level
        return main, alias, resolve_settings(self.request(main, trust), self.root)

    def test_original_main_alias_control(self):
        _, alias, settings = self.alias_settings()
        self.assertEqual((settings.trust, settings.trust_key), ('trusted', str(alias)))

    def test_canonical_main_key_precedes_alias_control(self):
        main, _, settings = self.alias_settings('untrusted')
        self.assertEqual((settings.trust, settings.trust_key), ('untrusted', str(main)))

    def malformed(self, slot):
        if slot == 'main_pointer':
            # Custom storage leaves main/.git available for a pointer file.
            main = self.base / 'main'
            main, common, _ = self.linked(main, main / 'storage')
            self.put(main / '.git', 'gitdir: ' + str(common) + '\0x\n')
        else:
            main, _, admin = self.linked()
            if slot == 'commondir':
                self.put(admin / slot, '../..\0x\n')
            else:
                # Parent canonicalization must reject NUL rather than allowing
                # Darwin c_char_p to truncate to the valid checkout prefix.
                self.put(admin / 'gitdir', str(self.root) + '\0x/.git\n')
        return self.request(main)

    def test_nul_commondir_is_unset_and_retains_readable_chain(self):
        request = self.malformed('commondir')
        self.assert_unset(request)
        self.assert_readable_chain(request)

    def test_nul_backlink_is_unset_and_retains_readable_chain(self):
        request = self.malformed('backlink')
        self.assert_unset(request)
        self.assert_readable_chain(request)

    def test_nul_main_pointer_is_unset_and_retains_readable_chain(self):
        request = self.malformed('main_pointer')
        self.assert_unset(request)
        self.assert_readable_chain(request)

    def test_nul_commondir_does_not_apply_project_settings(self):
        request = self.malformed('commondir')
        self.put(self.root / '.codex/config.toml',
                 'project_doc_max_bytes = 7\nproject_doc_fallback_filenames = ["LOCAL.md"]\n')
        settings = self.assert_unset(request)
        self.assertEqual(settings.limit, 1000)
        self.assertEqual(settings.fallback_names, ['BASE.md'])
        self.assert_readable_chain(request)

    def test_backlink_missing_component_collapses_before_lookup_control(self):
        main, _, admin = self.linked()
        backlink = self.root.parent / "missing/.." / self.root.name / ".git"
        self.put(admin / "gitdir", str(backlink) + "\n")
        settings = resolve_settings(self.request(main), self.root)
        self.assertEqual((settings.trust, settings.trust_key), ("trusted", str(main)))

    def test_commondir_missing_component_collapses_before_lookup_control(self):
        main, _, admin = self.linked()
        self.put(admin / "commondir", "missing/../../..\n")
        settings = resolve_settings(self.request(main), self.root)
        self.assertEqual((settings.trust, settings.trust_key), ("trusted", str(main)))


if __name__ == '__main__':
    unittest.main()
