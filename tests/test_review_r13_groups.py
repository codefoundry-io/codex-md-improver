"""R13 regression: explicit groups respect Git administration boundaries.

Authored for dedicated RED/GREEN execution; fixture methods are delegated, never
inherited, so discovery does not rerun the public fixture's test methods.
"""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_discovery as fixtures
import discovery
from discovery import scan


class ExcludedGroupMembers(unittest.TestCase):
    setUp = fixtures.DiscoveryTests.setUp
    put = fixtures.DiscoveryTests.put
    request = fixtures.DiscoveryTests.request
    cli = fixtures.DiscoveryTests.cli

    def settings(self, cwds, limit=4, trust='trusted'):
        return {
            'non_project': {'limit': 32768, 'fallback_names': [], 'root_markers': []},
            'trust': {str(self.root): 'trusted'},
            'client': {'name': 'r13-group-fixture'},
            'environment_groups': [{
                'id': 'ordered', 'cwds': [str(cwd) for cwd in cwds],
                'effective_loader_settings': {
                    'limit': limit, 'fallback_names': [], 'root_markers': [],
                    'trust': trust, 'provenance': {'fixture': 'r13'},
                },
            }],
        }

    def decoys(self, cwd):
        return [self.put(cwd / name, 'Excluded administration guidance.\n')
                for name in ('AGENTS.md', 'AGENTS.override.md')]

    def storage(self, external=False, alias=False):
        # Preserve the fixture's existing real .git directory; a nested checkout
        # identifies a separate administrative tree through a Git pointer.
        storage = (self.base if external else self.root) / 'admin-store'
        self.put(storage / 'HEAD', 'ref: refs/heads/main\n')
        decoys = self.decoys(storage)
        self.put(self.root / 'checkout/.git', 'gitdir: ' + str(storage) + '\n')
        if alias:
            cwd = self.root / 'admin-alias'
            cwd.symlink_to(storage, target_is_directory=True)
        else:
            cwd = storage
        return cwd, decoys

    def traced_scan(self, settings, forbidden):
        identities = {tuple(discovery._Content().identity(path)) for path in forbidden}
        reads = []
        original = discovery._Content.read

        def read(content, path):
            reads.append((str(path), tuple(content.identity(path))))
            return original(content, path)

        with patch.object(discovery._Content, 'read', read):
            report = scan(self.request(settings))
        self.assertEqual([path for path, identity in reads if identity in identities], [],
                         'Excluded AGENTS physical identities must never reach _Content.read')
        return report

    def assert_excluded(self, member, cwd, settings, zero=False):
        self.assertEqual(member['cwd'], str(cwd))
        self.assertEqual(member['inventory_root'], str(self.root))
        self.assertEqual(member['environment_group_id'], 'ordered')
        digest = hashlib.sha256(json.dumps([str(self.root), str(cwd)]).encode()).hexdigest()[:16]
        self.assertEqual(member['scenario_id'], 'group:ordered:' + digest)
        raw = settings['environment_groups'][0]['effective_loader_settings']
        for name in ('limit', 'fallback_names', 'root_markers', 'trust'):
            self.assertEqual(member['settings'][name], raw[name])
        self.assertEqual(member['settings']['client'], settings['client'])
        self.assertEqual(member['settings']['provenance']['scenario'], 'supplied_group_effective')
        self.assertEqual(member['settings']['provenance']['fixture'], 'r13')
        self.assertEqual(member['sources'], [])
        self.assertEqual(member['scope_sources'], [])
        self.assertFalse(member.get('global_source', {}).get('path'))
        self.assertTrue(member['partial'])
        self.assertEqual(member['discovery_error'], 'excluded_git')
        self.assertIsNone(member['modeled_loader_error'])
        self.assertIsNone(member['project_original_bytes'])
        self.assertIsNone(member['warning'])
        self.assertIsNone(member['raw_volume_exceeds_budget'])
        if zero:
            self.assertEqual(member['project_included_bytes'], 0)
            self.assertEqual(member['project_retained_raw_bytes'], 0)
        else:
            self.assertEqual(member['loader_outcome'], 'unresolved')
            self.assertIsNone(member['project_included_bytes'])
            self.assertIsNone(member['project_retained_raw_bytes'])

    def check_single(self, cwd, decoys, limit=4, trust='trusted'):
        settings = self.settings([cwd], limit, trust)
        report = self.traced_scan(settings, decoys)
        self.assert_excluded(report['groups'][0]['members'][0], cwd, settings,
                             zero=limit == 0 or trust == 'untrusted')
        self.assertTrue(report['partial'])
        self.assertEqual(report['exit_code'], 3)
        self.assertIn(str(self.root), {row['cwd'] for row in report['chains']})
        self.assertFalse(any(row['cwd'] == str(cwd) for row in report['chains']))
        return report

    def test_direct_git_cwd_is_unresolved_without_instruction_reads(self):
        cwd = self.root / '.git'
        self.check_single(cwd, self.decoys(cwd))

    def test_identified_in_tree_storage_cwd_is_excluded_before_reads(self):
        self.check_single(*self.storage())

    def test_identified_in_tree_storage_alias_uses_physical_boundary(self):
        self.check_single(*self.storage(alias=True))

    def test_external_identified_storage_in_tree_alias_is_excluded(self):
        self.check_single(*self.storage(external=True, alias=True))

    def test_unknown_budget_excluded_member_keeps_unknown_accounting(self):
        cwd = self.root / '.git'
        self.check_single(cwd, self.decoys(cwd), limit=None)

    def test_zero_and_untrusted_gates_do_not_read_excluded_guidance(self):
        cwd = self.root / '.git'
        decoys = self.decoys(cwd)
        for limit, trust in ((0, 'trusted'), (4, 'untrusted')):
            with self.subTest(limit=limit, trust=trust):
                self.check_single(cwd, decoys, limit=limit, trust=trust)

    def ordered(self, first_size=3):
        first, excluded, last = self.root / 'first', self.root / '.git', self.root / 'last'
        self.put(first / 'AGENTS.md', 'a' * first_size)
        self.put(last / 'AGENTS.md', 'bb')
        decoys = self.decoys(excluded)
        return [first, excluded, last], decoys

    def test_normal_excluded_normal_preserves_order_and_unknown_shared_budget(self):
        cwds, decoys = self.ordered()
        settings = self.settings(cwds)
        report = self.traced_scan(settings, decoys)
        group = report['groups'][0]
        members = group['members']
        self.assertEqual([member['cwd'] for member in members], list(map(str, cwds)))
        self.assertEqual(members[0]['project_included_bytes'], 3)
        self.assert_excluded(members[1], cwds[1], settings)
        self.assertIsNone(members[2]['project_included_bytes'])
        self.assertIsNone(members[2]['project_retained_raw_bytes'])
        self.assertEqual(members[2]['loader_outcome'], 'unresolved')
        self.assertEqual(members[2]['project_original_bytes'], 2)
        self.assertIsNone(group['project_included_bytes'])
        self.assertIsNone(group['project_original_bytes'])
        self.assertIsNone(group['warning'])
        self.assertEqual(group['possible_outcomes'], ['unresolved'])
        self.assertEqual({Path(row['cwd']).name: row['project_included_bytes']
                          for row in report['chains']}['last'], 2)

    def test_exhausted_shared_budget_stays_zero_without_excluded_reads(self):
        cwds, decoys = self.ordered(first_size=4)
        settings = self.settings(cwds)
        report = self.traced_scan(settings, decoys)
        members = report['groups'][0]['members']
        self.assertEqual([member['project_included_bytes'] for member in members], [4, 0, 0])
        self.assert_excluded(members[1], cwds[1], settings, zero=True)
        self.assertEqual(members[2]['loader_outcome'], 'budget_exhausted')

    def test_cli_excluded_members_have_no_global_or_project_graph_seeds(self):
        cwds, decoys = self.ordered()
        global_source = self.put(self.home / 'AGENTS.md', 'Global guidance.\n')
        settings = self.settings(cwds)
        proc, report = self.cli(settings)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        members = report['groups'][0]['members']
        self.assert_excluded(members[1], cwds[1], settings)
        scenario = members[1]['scenario_id']
        self.assertEqual(report['graph']['roots'].get(scenario, []), [])
        self.assertFalse(any(row['scenario_id'] == scenario for row in report['graph']['occurrences']))
        self.assertFalse(any(str(path) in node['aliases'] for path in decoys
                             for node in report['graph']['nodes'].values()))
        self.assertFalse(any(candidate['path'] in set(map(str, decoys))
                             for candidate in report['candidates']))
        self.assertTrue(any(str(global_source) in node['aliases']
                            for node in report['graph']['nodes'].values()))
        for member in (members[0], members[2]):
            self.assertTrue(report['graph']['roots'][member['scenario_id']])
        self.assertIn(str(self.root), {row['cwd'] for row in report['chains']})

    def test_normal_group_and_ordinary_sibling_prefix_keep_shared_budget(self):
        storage, _ = self.storage()
        first = storage.with_name(storage.name + '-ordinary')
        last = self.root / 'last'
        self.put(first / 'AGENTS.md', 'aaa')
        self.put(last / 'AGENTS.md', 'bb')
        settings = self.settings([first, last])
        report = scan(self.request(settings))
        members = report['groups'][0]['members']
        self.assertEqual([member['cwd'] for member in members], [str(first), str(last)])
        self.assertEqual([member['project_included_bytes'] for member in members], [3, 1])
        self.assertTrue(all(member['discovery_error'] is None for member in members))
        self.assertFalse(report['partial'])
        self.assertIn(str(first), {row['cwd'] for row in report['chains']})


if __name__ == '__main__':
    unittest.main()
