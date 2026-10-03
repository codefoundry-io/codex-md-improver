"""Canonical Git validation retains the original validated main trust alias."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
from discovery import ScopeRequest, resolve_settings


class OriginalMainTrustAlias(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def settings(self, redundant=False, canonical_trust=None):
        main = self.base / 'main-real'
        alias = self.base / 'main-alias'
        admin = main / '.git/worktrees/linked'
        self.put(main / '.git/HEAD', 'ref: refs/heads/main\n')
        self.put(admin / 'gitdir', str(self.root / '.git') + '\n')
        self.put(admin / 'commondir', '../..\n')
        (main / '.git/spare').mkdir()
        alias.symlink_to(main, target_is_directory=True)
        pointer = alias / ('.git/spare/../worktrees/linked' if redundant else '.git/worktrees/linked')
        self.put(self.root / '.git', 'gitdir: ' + str(pointer) + '\n')
        trust = {str(alias): 'trusted'}
        if canonical_trust is not None:
            trust[str(main)] = canonical_trust
        request = ScopeRequest([self.root], self.home, self.root, {'trust': trust})
        return main, alias, resolve_settings(request, self.root)

    def test_main_checkout_alias_trust_is_preserved(self):
        _, alias, settings = self.settings()
        self.assertEqual(settings.trust, 'trusted')
        self.assertEqual(settings.trust_key, str(alias))

    def test_main_alias_with_redundant_administration_parent_is_preserved(self):
        _, alias, settings = self.settings(redundant=True)
        self.assertEqual(settings.trust, 'trusted')
        self.assertEqual(settings.trust_key, str(alias))

    def test_canonical_main_trust_still_precedes_alias_control(self):
        main, _, settings = self.settings(canonical_trust='untrusted')
        self.assertEqual(settings.trust, 'untrusted')
        self.assertEqual(settings.trust_key, str(main))

    def test_missing_lexical_main_does_not_hide_valid_canonical_trust_control(self):
        main = self.base / 'outer/realmain'
        admin = main / '.git/worktrees/linked'
        self.put(main / '.git/HEAD', 'ref: refs/heads/main\n')
        self.put(admin / 'gitdir', str(self.root / '.git') + '\n')
        self.put(admin / 'commondir', '../..\n')
        child = self.base / 'outer/child'
        child.mkdir()
        (self.root / 'bridge').symlink_to(child, target_is_directory=True)
        pointer = self.root / 'bridge/../realmain/.git/worktrees/linked'
        self.assertEqual(pointer.resolve(strict=True), admin)
        self.assertFalse((self.root / 'realmain').exists())
        self.put(self.root / '.git', 'gitdir: ' + str(pointer) + '\n')
        request = ScopeRequest([self.root], self.home, self.root, {'trust': {str(main): 'trusted'}})
        settings = resolve_settings(request, self.root)
        self.assertEqual(settings.trust, 'trusted')
        self.assertEqual(settings.trust_key, str(main))
