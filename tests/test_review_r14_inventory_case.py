"""Native inventory containment preserves aliases and scenario spelling."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
from discovery import _Content
import md_improver


class NativeInventoryContainment(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def tree(self):
        stored = self.base / 'MixedRepo'
        self.put(stored / '.git/HEAD', 'ref: refs/heads/main\n')
        self.put(stored / 'AGENTS.md', 'Root guidance.\n')
        self.put(stored / 'sub/AGENTS.md', 'Read [guide](docs/guide.md).\n')
        self.put(stored / 'sub/docs/guide.md', 'Relative guidance leaf.\n')
        (stored / 'sub/deep').mkdir()
        return stored

    def native_alias(self, stored):
        alias = stored.with_name('mixedrepo')
        if not alias.exists():
            self.skipTest('fixture volume lacks the native case alias')
        self.assertNotEqual(str(alias), str(stored))
        self.assertTrue(alias.samefile(stored))
        self.assertTrue((alias / 'sub').samefile(stored / 'sub'))
        return alias

    def run_cli(self, selected, trust):
        settings = self.put(self.base / 'settings.json', json.dumps({
            'non_project': {'limit': 32768, 'fallback_names': [], 'root_markers': ['.git']},
            'trust': trust,
        }))
        out = self.base / 'out'
        code = md_improver.main([
            'scan', '--project', str(selected), '--codex-home', str(self.home),
            '--settings', str(settings), '--out', str(out),
        ])
        audit = json.loads((out / 'audit.json').read_text())
        routes = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
        return code, audit, routes

    def assert_inside_alias(self, code, audit, routes, selected, alias, leaf):
        self.assertEqual(code, 0)
        self.assertFalse(audit['partial'])
        self.assertTrue(audit['inventory_complete'])
        self.assertFalse(any(frontier['kind'] == 'outside_scope' for frontier in audit['frontiers']))
        by_cwd = {row['cwd']: row for row in audit['chains']}
        for cwd in (alias, alias / 'deep'):
            self.assertIn(str(cwd), by_cwd)
            row = by_cwd[str(cwd)]
            self.assertEqual(row['cwd'], str(cwd))
            self.assertEqual(row['inventory_root'], str(selected))
            self.assertIsNone(row['discovery_error'])
            self.assertFalse(row['partial'])
            relative_routes = [route for route in routes
                               if route['scenario_id'] == row['scenario_id']
                               and route['terminal_kind'] == 'leaf'
                               and Path(route['terminal_path']).samefile(leaf)]
            self.assertTrue(relative_routes, 'Alias scenario lost its relative document route')
            self.assertTrue(any(Path(route['terminal_path']).is_relative_to(alias)
                                for route in relative_routes))
        return by_cwd

    def test_stored_root_keeps_alias_target_using_different_case_spelling(self):
        stored = self.tree()
        case_root = self.native_alias(stored)
        alias = stored / 'alias'
        alias.symlink_to(case_root / 'sub', target_is_directory=True)
        self.assertTrue(alias.samefile(stored / 'sub'))
        code, audit, routes = self.run_cli(stored, {str(stored): 'trusted'})
        rows = self.assert_inside_alias(code, audit, routes, stored, alias,
                                       stored / 'sub/docs/guide.md')
        self.assertEqual(rows[str(alias)]['settings']['trust'], 'trusted')
        self.assertEqual(rows[str(alias)]['settings']['trust_key'], str(stored))

    def test_case_alias_selected_root_keeps_stored_spelling_target_and_trust(self):
        stored = self.tree()
        selected = self.native_alias(stored)
        alias = selected / 'alias'
        alias.symlink_to(stored / 'sub', target_is_directory=True)
        self.assertTrue(alias.samefile(stored / 'sub'))
        # Native canonical trust wins; the lexical selected root remains the
        # report's owner and cwd spelling rather than being rewritten.
        code, audit, routes = self.run_cli(selected, {
            str(stored): 'trusted', str(selected): 'untrusted',
        })
        rows = self.assert_inside_alias(code, audit, routes, selected, alias,
                                       stored / 'sub/docs/guide.md')
        self.assertIn(str(selected), rows)
        self.assertEqual(rows[str(selected)]['cwd'], str(selected))
        self.assertEqual(rows[str(selected)]['inventory_root'], str(selected))
        self.assertEqual(rows[str(selected)]['settings']['trust'], 'trusted')
        self.assertEqual(rows[str(selected)]['settings']['trust_key'], str(stored))

    def test_same_spelling_in_scope_alias_control_retains_descendants_and_routes(self):
        stored = self.tree()
        alias = stored / 'alias'
        alias.symlink_to(stored / 'sub', target_is_directory=True)
        self.assertTrue(alias.samefile(stored / 'sub'))
        code, audit, routes = self.run_cli(stored, {str(stored): 'trusted'})
        self.assert_inside_alias(code, audit, routes, stored, alias,
                                 stored / 'sub/docs/guide.md')

    def test_truly_outside_alias_stays_partial_without_guidance_reads(self):
        stored = self.tree()
        outside = self.base / 'OutsideRepo'
        source = self.put(outside / 'AGENTS.md', 'Outside guidance must remain unread.\n')
        alias = stored / 'outside-alias'
        alias.symlink_to(outside, target_is_directory=True)
        self.assertTrue(alias.samefile(outside))
        forbidden_identity = tuple(_Content().identity(source))
        reads = []
        original = _Content.read

        def track(content, path):
            if tuple(content.identity(path)) == forbidden_identity:
                reads.append(str(path))
            return original(content, path)

        with patch.object(_Content, 'read', track):
            code, audit, routes = self.run_cli(stored, {str(stored): 'trusted'})
        self.assertEqual(reads, [])
        self.assertEqual(code, 3)
        self.assertTrue(audit['partial'])
        self.assertFalse(audit['inventory_complete'])
        self.assertIn({'path': str(alias), 'kind': 'outside_scope'}, audit['frontiers'])
        self.assertFalse(any(Path(row['cwd']).is_relative_to(alias) for row in audit['chains']))
        self.assertFalse(any(Path(row['cwd']).is_relative_to(outside) for row in audit['chains']))
        self.assertFalse(any(str(alias / 'AGENTS.md') in node['aliases'] or str(source) in node['aliases']
                             for node in audit['graph']['nodes'].values()))
        self.assertFalse(any(Path(route['terminal_path']).samefile(source)
                             for route in routes if route['terminal_kind'] == 'leaf'))


if __name__ == '__main__':
    unittest.main()
