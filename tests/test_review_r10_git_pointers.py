"""Untrusted Git pointers cannot erase a selected project inventory."""
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
import md_improver


class PointerScope(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def run_pointer(self, marker, target, projects=None, cwd=False, symlink=False):
        projects = projects or [self.root]
        self.put(self.home / 'AGENTS.md', 'Global baseline.')
        if symlink:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.symlink_to(target, target_is_directory=True)
        else:
            self.put(marker, 'gitdir: ' + target + '\n')
        settings = self.put(self.base / 'settings.json', json.dumps({
            'non_project': {'limit': 32768, 'root_markers': ['.git'], 'fallback_names': []},
            'trust': {str(root): 'trusted' for root in projects}}))
        out = self.base / ('out-' + str(len(list(self.base.glob('out-*')))))
        args = ['scan', '--codex-home', str(self.home), '--settings', str(settings), '--out', str(out)]
        for root in projects: args += ['--project', str(root)]
        if cwd: args += ['--cwd', str(self.root)]
        code = md_improver.main(args)
        return code, json.loads((out / 'audit.json').read_text())

    def check_invalid(self, marker, target, projects=None, cwd=False, symlink=False):
        code, audit = self.run_pointer(marker, target, projects, cwd, symlink)
        with self.subTest(check='partial instead of false complete'):
            self.assertEqual(code, 3)
            self.assertTrue(audit['partial'])
            self.assertFalse(audit['inventory_complete'])
        with self.subTest(check='selected projects retained'):
            cwds = {row['cwd'] for row in audit['chains']}
            for root in projects or [self.root]: self.assertIn(str(root), cwds)
        with self.subTest(check='invalid pointer frontier'):
            self.assertTrue(any(f['path'] == str(marker) and f['kind'] == 'blocked'
                                and f.get('error') == 'invalid_git_pointer' for f in audit['frontiers']))
        if symlink:
            with self.subTest(check='invalid alias must not reenter graph storage roots'):
                self.assertFalse(any(f['path'] == str(marker) and f['kind'] == 'git_administration'
                                     for f in audit['frontiers']))
            with self.subTest(check='project source remains reachable by graph'):
                self.assertTrue(any(str(self.source) in node['aliases'] for node in audit['graph']['nodes'].values()))

    def test_self_pointer_preserves_root_inventory(self):
        self.check_invalid(self.root / '.git', '.')

    def test_self_pointer_preserves_explicit_cwd(self):
        self.check_invalid(self.root / '.git', '.', cwd=True)

    def test_nested_pointer_cannot_exclude_project_ancestor(self):
        self.check_invalid(self.root / 'vendor/x/.git', '../..')

    def test_pointer_cannot_exclude_another_selected_project(self):
        other = self.base / 'other'
        self.put(other / 'AGENTS.md', 'Other selected project.')
        self.check_invalid(self.root / '.git', str(other), [self.root, other])

    def test_directory_symlink_marker_to_self_retains_inventory_and_graph(self):
        self.check_invalid(self.root / '.git', '.', symlink=True)

    def test_directory_symlink_marker_to_self_retains_explicit_cwd(self):
        self.check_invalid(self.root / '.git', '.', cwd=True, symlink=True)

    def test_directory_symlink_marker_cannot_erase_other_selected_root(self):
        other = self.base / 'other'
        self.put(other / 'AGENTS.md', 'Other selected project.')
        self.check_invalid(self.root / '.git', str(other), [self.root, other], symlink=True)

    def test_valid_external_storage_control(self):
        storage = self.base / 'GitStore'
        self.put(storage / 'HEAD', 'ref: refs/heads/main\n')
        code, audit = self.run_pointer(self.root / '.git', '../GitStore')
        self.assertEqual(code, 0)
        self.assertIn(str(self.root), {row['cwd'] for row in audit['chains']})
        self.assertTrue(any(f == {'path': str(storage), 'kind': 'git_administration'}
                            for f in audit['frontiers']))

    def test_valid_external_directory_symlink_storage_control(self):
        storage = self.base / 'GitStore'
        self.put(storage / 'HEAD', 'ref: refs/heads/main\n')
        code, audit = self.run_pointer(self.root / '.git', '../GitStore', symlink=True)
        self.assertEqual(code, 0)
        self.assertIn(str(self.root), {row['cwd'] for row in audit['chains']})
        self.assertTrue(any(f == {'path': str(storage), 'kind': 'git_administration'}
                            for f in audit['frontiers']))

    def test_existing_in_tree_sibling_storage_contract_is_preserved(self):
        storage = self.root / 'admin'
        self.put(storage / 'AGENTS.md', 'Git storage content, not an instruction chain.')
        code, audit = self.run_pointer(self.root / '.git', 'admin')
        self.assertEqual(code, 0)
        self.assertNotIn(str(storage), {row['cwd'] for row in audit['chains']})
        self.assertIn(str(self.root), {row['cwd'] for row in audit['chains']})
