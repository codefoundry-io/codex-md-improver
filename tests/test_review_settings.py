"""Scenario identity, uncertain settings and source provenance regressions."""
from dataclasses import asdict
from pathlib import Path
import unittest
from unittest.mock import patch
import test_discovery as discovery_fixtures
import test_references as reference_fixtures
from discovery import resolve_settings, discover_chains, scan


class SettingsReview(unittest.TestCase):
    setUp = discovery_fixtures.DiscoveryTests.setUp
    put = discovery_fixtures.DiscoveryTests.put
    trust = discovery_fixtures.DiscoveryTests.trust
    request = discovery_fixtures.DiscoveryTests.request
    chain = discovery_fixtures.DiscoveryTests.chain

    def test_unknown_project_eligibility_keeps_budget_and_fallback_uncertain(self):
        self.put(self.root / 'AGENTS.md', 'x' * 40000)
        self.put(self.root / '.codex/config.toml', 'project_doc_max_bytes = 65536\n')
        unknown = {'trust': {str(self.root): 'unknown'}}
        row = self.chain(settings=unknown)
        self.assertIsNone(row['warning'])
        self.assertIsNone(row['raw_volume_exceeds_budget'])
        self.assertIsNone(row['project_included_bytes'])
        trusted = self.chain(settings={'trust': {str(self.root): 'trusted'}})
        self.assertEqual((trusted['warning'], trusted['raw_volume_exceeds_budget']), (False, False))
        explicit = self.chain(settings={**unknown, 'session_overrides': {'limit': 65536}})
        self.assertEqual((explicit['warning'], explicit['raw_volume_exceeds_budget']), (False, False))
        self.put(self.root / '.codex/config.toml', 'project_doc_fallback_filenames = ["GUIDE.md"]\n')
        (self.root / 'AGENTS.md').unlink()
        self.put(self.root / 'GUIDE.md', 'fallback instructions')
        row = self.chain(settings=unknown)
        self.assertIsNone(row['settings']['fallback_names'])
        self.assertIsNone(row['project_original_bytes'])

    def test_unknown_trust_denied_layer_is_not_confirmed_absence(self):
        config = self.put(self.root / '.codex/config.toml', 'project_doc_max_bytes = 65536\n')
        original_read = Path.read_bytes
        def read(path):
            if path == config:
                raise PermissionError('injected project config denial')
            return original_read(path)
        with patch.object(Path, 'read_bytes', read):
            result = resolve_settings(self.request({'trust': {str(self.root): 'unknown'}}), self.root)
        self.assertIsNone(result.limit)
        self.assertIsNone(result.fallback_names)
        config.unlink()
        absent = resolve_settings(self.request({'trust': {str(self.root): 'unknown'}}), self.root)
        self.assertEqual(absent.limit, 32768)
        self.assertEqual(absent.fallback_names, [])

    def test_nested_roots_have_distinct_inventory_scenario_ids(self):
        child = self.root / 'app'
        self.put(child / 'AGENTS.md', 'child instructions')
        report = scan(self.request(projects=[self.root, child]))
        rows = [c for c in report['chains'] if c['cwd'] == str(child)]
        self.assertEqual({c['inventory_root'] for c in rows}, {str(self.root), str(child)})
        self.assertEqual(len({c['scenario_id'] for c in rows}), 2)
        duplicate = discover_chains(self.request(projects=[self.root, self.root]))
        self.assertEqual(len({(c['cwd'], c['inventory_root']) for c in duplicate}), len(duplicate))

    def test_supplied_client_and_winning_settings_provenance_survive(self):
        client = {'name': 'Codex', 'version': 'fixture-version'}
        default = asdict(resolve_settings(self.request({'client': client}), self.root))
        self.assertEqual(default.get('client'), client)
        self.assertEqual(default['provenance'].get('fields', {}).get('limit'), 'pinned_default')
        self.trust(extra='project_doc_max_bytes = 100\n')
        observed = asdict(resolve_settings(self.request({'client': client}), self.root))
        self.assertEqual(observed['provenance'].get('fields', {}).get('limit'), 'observed_user_config')
        supplied = asdict(resolve_settings(self.request({'non_project': {'limit': 90}}), self.root))
        self.assertEqual(supplied['provenance'].get('fields', {}).get('limit'), 'supplied_non_project')
        config = self.put(self.root / '.codex/config.toml', 'project_doc_max_bytes = 80\nproject_root_markers = []\n')
        project = asdict(resolve_settings(self.request(), self.root))
        self.assertEqual(project['provenance'].get('fields', {}).get('limit'), 'trusted_project:' + str(config))
        self.assertEqual(project['provenance'].get('fields', {}).get('root_markers'), 'pinned_default')
        overridden = asdict(resolve_settings(self.request({'session_overrides': {'limit': 70}}), self.root))
        self.assertEqual(overridden['provenance'].get('fields', {}).get('limit'), 'supplied_session_override')
        group = {'id': 'group', 'cwds': [str(self.root)], 'effective_loader_settings': {
            'limit': 50, 'fallback_names': [], 'root_markers': ['.git'], 'trust': 'trusted',
            'provenance': {'fields': {'limit': 'owner supplied controlling session'}}}}
        result = scan(self.request({'client': client, 'environment_groups': [group]}))
        effective = result['groups'][0]['members'][0]['settings']
        self.assertEqual(effective.get('client'), client)
        self.assertEqual(effective['provenance']['fields']['limit'], 'owner supplied controlling session')
        self.assertFalse(default['provenance']['live_runtime_attested'])


class ReferenceSummaryReview(unittest.TestCase):
    setUp = reference_fixtures.ReferenceTests.setUp
    put = reference_fixtures.ReferenceTests.put
    chain = reference_fixtures.ReferenceTests.chain
    build = reference_fixtures.ReferenceTests.build
    routes = reference_fixtures.ReferenceTests.routes
    decision = reference_fixtures.ReferenceTests.decision

    def test_directory_subtotals_keep_scenario_identity_and_physical_union(self):
        shared = self.base / 'shared'
        guide = self.put(shared / 'guide.md', 'Read `leaf.md`.\n')
        a = self.put(self.root / 'a/leaf.md', 'A')
        b = self.put(self.root / 'b/leaf.md', 'B' * 20)
        self.put(self.source, '[shared](' + str(shared) + ')\n')
        chains = [self.chain(a.parent, scenario='a'), self.chain(b.parent, scenario='b')]
        graph = self.build(chains, {str(guide): {'kind': 'scenario_cwd'}})
        size = guide.stat().st_size
        by_scenario = graph.get('directory_totals_by_scenario', {})
        self.assertEqual(by_scenario.get('a', {}).get(str(shared)), size + 1)
        self.assertEqual(by_scenario.get('b', {}).get(str(shared)), size + 20)
        self.assertEqual(graph['directory_totals'][str(shared)], size + 1 + 20)

    def test_unquoted_version_and_abbreviation_are_not_path_dependencies(self):
        self.put(self.source, 'Use Python 3.11+.\nUse e.g. snake_case.\nExample e.g. `sample.md`.\n')
        graph = self.build(resolutions=[self.decision('sample.md', 'example')])
        self.assertFalse(graph['partial'])
        self.assertFalse(any(e['target_text'] in {'3.11', 'e.g'} for e in graph['occurrences']))
        # Explicit numeric filenames remain legitimate paths, not runtime versions.
        self.put(self.source, '[numeric](./3.11)\n')
        numeric = self.put(self.root / '3.11', 'numeric filename')
        self.assertIn(str(numeric), {r['terminal_path'] for r in self.routes(self.build())})


if __name__ == '__main__':
    unittest.main()
