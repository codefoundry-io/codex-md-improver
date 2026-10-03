"""Filesystem-significant dot-dot in Git pointers preserves inventory and trust."""
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
import md_improver
from discovery import ScopeRequest, resolve_settings


class GitPointerPaths(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def inventory(self, pointer):
        self.put(self.home / 'AGENTS.md', 'Global baseline.')
        self.put(self.root / '.git', 'gitdir: ' + pointer + '\n')
        settings = self.put(self.base / 'settings.json', json.dumps({
            'non_project': {'limit': 32768, 'root_markers': ['.git'], 'fallback_names': []},
            'trust': {str(self.root): 'trusted'}}))
        out = self.base / 'out'
        code = md_improver.main(['scan', '--project', str(self.root), '--codex-home',
                                str(self.home), '--settings', str(settings), '--out', str(out)])
        return code, json.loads((out / 'audit.json').read_text())

    def check_inventory(self, absolute):
        child = self.root / 'actual/child'
        child.mkdir(parents=True)
        (self.root / 'alias').symlink_to('actual/child', target_is_directory=True)
        storage = self.root / 'actual/store'
        self.put(storage / 'HEAD', 'ref: refs/heads/main\n')
        (storage / 'objects').mkdir()
        (storage / 'refs').mkdir()
        self.put(storage / 'AGENTS.md', 'Administrative decoy.')
        ordinary = self.put(self.root / 'store/AGENTS.md', 'Ordinary instruction subtree.')
        pointer = str(self.root / 'alias/../store') if absolute else 'alias/../store'
        self.assertEqual((self.root / pointer).resolve(strict=True), storage)
        code, audit = self.inventory(pointer)
        with self.subTest(check='successful complete scan'):
            self.assertEqual(code, 0)
            self.assertFalse(audit['partial'])
            self.assertTrue(audit['inventory_complete'])
        with self.subTest(check='ordinary subtree retained'):
            self.assertIn(str(ordinary.parent), {c['cwd'] for c in audit['chains']})
            self.assertTrue(any(str(ordinary) in n['aliases'] for n in audit['graph']['nodes'].values()))
        with self.subTest(check='actual storage excluded'):
            self.assertNotIn(str(storage), {c['cwd'] for c in audit['chains']})
            self.assertIn({'path': str(storage), 'kind': 'git_administration'}, audit['frontiers'])
            self.assertFalse(any(str(storage / 'AGENTS.md') in n['aliases']
                                 for n in audit['graph']['nodes'].values()))

    def test_relative_symlink_parent_pointer_keeps_ordinary_inventory(self):
        self.check_inventory(False)

    def test_absolute_symlink_parent_pointer_keeps_ordinary_inventory(self):
        self.check_inventory(True)

    def worktree(self, style, mismatch=False):
        main = self.base / 'main'
        admin = main / '.git/worktrees/linked'
        self.put(main / '.git/HEAD', 'ref: refs/heads/main\n')
        self.put(admin / 'gitdir', str((main if mismatch else self.root) / '.git') + '\n')
        self.put(admin / 'commondir', '../..\n')
        if style == 'simple':
            pointer = '../main/.git/worktrees/linked'
        else:
            child = main / '.git/worktrees/child'
            child.mkdir()
            (self.root / 'bridge').symlink_to(child, target_is_directory=True)
            pointer = str(self.root / 'bridge/../linked') if style == 'absolute' else 'bridge/../linked'
        self.put(self.root / '.git', 'gitdir: ' + pointer + '\n')
        self.assertEqual((self.root / pointer).resolve(strict=True), admin)
        request = ScopeRequest([self.root], self.home, self.root, {'trust': {str(main): 'trusted'}})
        return main, resolve_settings(request, self.root)

    def test_relative_symlink_parent_worktree_trust(self):
        main, settings = self.worktree('relative')
        self.assertEqual(settings.trust, 'trusted')
        self.assertEqual(settings.trust_key, str(main))

    def test_absolute_symlink_parent_worktree_trust(self):
        main, settings = self.worktree('absolute')
        self.assertEqual(settings.trust, 'trusted')
        self.assertEqual(settings.trust_key, str(main))

    def test_simple_relative_worktree_control(self):
        main, settings = self.worktree('simple')
        self.assertEqual(settings.trust, 'trusted')
        self.assertEqual(settings.trust_key, str(main))

    def test_mismatched_backlink_stays_untrusted_control(self):
        _, settings = self.worktree('relative', mismatch=True)
        self.assertEqual(settings.trust, 'unset')
        self.assertIsNone(settings.trust_key)

    def test_symlink_parent_ancestor_pointer_remains_blocked(self):
        (self.root / 'child').mkdir()
        (self.root / 'alias').symlink_to('child', target_is_directory=True)
        code, audit = self.inventory('alias/..')
        self.assertEqual(code, 3)
        self.assertTrue(audit['partial'])
        self.assertIn(str(self.root), {c['cwd'] for c in audit['chains']})
        self.assertTrue(any(f['path'] == str(self.root / '.git')
                            and f.get('error') == 'invalid_git_pointer' for f in audit['frontiers']))

    def test_benign_actual_parent_does_not_reject_selected_root(self):
        (self.root / 'admin/child').mkdir(parents=True)
        (self.root / 'alias').symlink_to('admin/child', target_is_directory=True)
        code, audit = self.inventory('alias/..')
        self.assertEqual(code, 0)
        self.assertFalse(audit['partial'])
        self.assertIn(str(self.root), {c['cwd'] for c in audit['chains']})
        self.assertIn({'path': str(self.root / 'admin'), 'kind': 'git_administration'}, audit['frontiers'])

    def test_missing_component_before_parent_never_excludes_lexical_decoy(self):
        ordinary = self.put(self.root / 'store/AGENTS.md', 'Ordinary instructions.')
        code, audit = self.inventory('missing/../store')
        self.assertEqual(code, 0)
        self.assertIn(str(ordinary.parent), {c['cwd'] for c in audit['chains']})
        self.assertFalse(any(f == {'path': str(ordinary.parent), 'kind': 'git_administration'}
                             for f in audit['frontiers']))

    def test_main_checkout_pointer_preserves_significant_parent(self):
        main = self.base / 'main'
        common = main / 'storage'
        admin = common / 'worktrees/linked'
        self.put(admin / 'gitdir', str(self.root / '.git') + '\n')
        self.put(admin / 'commondir', '../..\n')
        (common / 'child').mkdir()
        (main / 'alias').symlink_to('storage/child', target_is_directory=True)
        self.put(main / '.git', 'gitdir: alias/..\n')
        self.put(self.root / '.git', 'gitdir: ' + str(admin) + '\n')
        request = ScopeRequest([self.root], self.home, self.root, {'trust': {str(main): 'trusted'}})
        settings = resolve_settings(request, self.root)
        self.assertEqual(settings.trust, 'trusted')
        self.assertEqual(settings.trust_key, str(main))
