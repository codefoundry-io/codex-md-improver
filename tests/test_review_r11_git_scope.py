"""Explicit cwd and non-directory Git aliases cannot erase readable guidance."""
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
import md_improver


class GitSelectedScope(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def scan(self, cwd=None):
        self.put(self.home / 'AGENTS.md', 'Global baseline.')
        settings = self.put(self.base / 'settings.json', json.dumps({
            'non_project': {'limit': 32768, 'root_markers': ['.git'], 'fallback_names': []},
            'trust': {str(self.root): 'trusted', str(cwd or self.root): 'trusted'}}))
        out = self.base / 'out'
        args = ['scan', '--project', str(self.root), '--codex-home', str(self.home),
                '--settings', str(settings), '--out', str(out)]
        if cwd: args += ['--cwd', str(cwd)]
        code = md_improver.main(args)
        return code, json.loads((out / 'audit.json').read_text())

    def check_cwd(self, symlink, ancestor=False, outer=False):
        cwd = self.root / ('sub/deep' if ancestor else 'sub')
        source = self.put(cwd / 'AGENTS.md', 'Selected local guidance.')
        target = cwd.parent if ancestor else cwd
        marker = (self.base if outer else self.root) / '.git'
        if symlink:
            marker.symlink_to(target, target_is_directory=True)
        else:
            self.put(marker, 'gitdir: ' + str(target) + '\n')
        code, audit = self.scan(cwd)
        with self.subTest(check='partial coverage'):
            self.assertEqual(code, 3)
            self.assertTrue(audit['partial'])
            self.assertFalse(audit['inventory_complete'])
        with self.subTest(check='selected cwd retained'):
            self.assertEqual([c['cwd'] for c in audit['chains']], [str(cwd)])
            self.assertTrue(any(str(source) in n['aliases'] for n in audit['graph']['nodes'].values()))
        with self.subTest(check='invalid marker is not administration'):
            self.assertTrue(any(f['path'] == str(marker) and f.get('error') == 'invalid_git_pointer'
                                for f in audit['frontiers']))
            self.assertNotIn({'path': str(marker), 'kind': 'git_administration'}, audit['frontiers'])

    def test_pointer_to_explicit_cwd_preserves_selected_chain(self):
        self.check_cwd(False)

    def test_directory_alias_to_explicit_cwd_preserves_selected_chain(self):
        self.check_cwd(True)

    def test_pointer_to_cwd_ancestor_preserves_selected_chain(self):
        self.check_cwd(False, ancestor=True)

    def test_directory_alias_to_cwd_ancestor_preserves_selected_chain(self):
        self.check_cwd(True, ancestor=True)

    def test_marker_above_project_cannot_erase_explicit_cwd(self):
        self.check_cwd(False, outer=True)

    def test_file_alias_marker_does_not_promote_guidance_to_storage(self):
        self.put(self.source, 'Read [docs](docs/).')
        policy = self.put(self.root / 'docs/policy.md', 'Readable project guidance.')
        marker = self.root / '.git'
        marker.symlink_to('docs/policy.md')
        code, audit = self.scan()
        with self.subTest(check='invalid marker is visible'):
            self.assertEqual(code, 3)
            self.assertTrue(audit['partial'])
            self.assertTrue(any(f['path'] == str(marker) and f.get('error') == 'invalid_git_pointer'
                                for f in audit['frontiers']))
        with self.subTest(check='ordinary directory child stays readable'):
            self.assertTrue(any(str(policy) in n['aliases'] for n in audit['graph']['nodes'].values()))
            self.assertNotIn({'path': str(marker), 'kind': 'git_administration'}, audit['frontiers'])

    def test_real_git_directory_and_selected_cwd_control(self):
        self.put(self.root / '.git/HEAD', 'ref: refs/heads/main\n')
        cwd = self.root / 'sub'
        source = self.put(cwd / 'AGENTS.md', 'Selected guidance.')
        code, audit = self.scan(cwd)
        self.assertEqual(code, 0)
        self.assertEqual([c['cwd'] for c in audit['chains']], [str(cwd)])
        self.assertTrue(any(str(source) in n['aliases'] for n in audit['graph']['nodes'].values()))
