"""Discovery-to-route and post-validation directory coverage integration."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path('/Users/chaniri/codex_workspace/workspace/codex-md-improver')
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_discovery as discovery_fixtures
import test_references as reference_fixtures
from discovery import _Content, scan
from references import build_reference_graph, iter_terminal_paths
import md_improver


class PrefixIntegration(unittest.TestCase):
    setUp = discovery_fixtures.DiscoveryTests.setUp
    put = discovery_fixtures.DiscoveryTests.put
    request = discovery_fixtures.DiscoveryTests.request

    def analyze(self, cwd, trust='trusted'):
        settings = {'non_project': {'limit': 1000, 'root_markers': ['.git'], 'fallback_names': []},
                    'trust': {str(self.root): trust, str(cwd): trust}}
        report = scan(self.request(settings, cwd))
        chain = next(c for c in report['chains'] if c['cwd'] == str(cwd))
        graph = build_reference_graph(report['chains'],
                                      context={'codex_home': self.home, 'user_home': self.home})
        return report, chain, graph, list(iter_terminal_paths(graph, chain))

    def test_omitted_ancestor_prefix_marks_readable_child_route_lower_bound(self):
        blocked = self.put(self.root / 'AGENTS.override.md', 'unknown ancestor')
        child = self.put(self.root / 'child/AGENTS.md', 'Read [leaf](leaf.md).\n')
        leaf = self.put(child.parent / 'leaf.md', 'readable leaf')
        original = Path.stat
        def stat(path, *args, **kwargs):
            if path == blocked:
                raise PermissionError('synthetic ancestor metadata denial')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'stat', stat):
            report, chain, graph, rows = self.analyze(child.parent)
        self.assertEqual(chain['sources'], [])
        self.assertIsNone(chain['project_original_bytes'])
        self.assertTrue(any(s['path'] == str(child) and s['selected'] is False for s in chain['scope_sources']))
        self.assertTrue(report['partial'])
        row = next(r for r in rows if r['terminal_path'] == str(leaf))
        self.assertEqual((row['terminal_kind'], row['content_status']), ('leaf', 'read'))
        self.assertEqual(row['route_original_bytes'], child.stat().st_size + leaf.stat().st_size)
        self.assertTrue(row['lower_bound'])

    def test_all_failed_global_selection_marks_known_project_route_lower_bound(self):
        blocked = {self.put(self.home / name, 'unknown global')
                   for name in ('AGENTS.override.md', 'AGENTS.md')}
        source = self.put(self.root / 'AGENTS.md', 'Read [leaf](leaf.md).\n')
        leaf = self.put(self.root / 'leaf.md', 'readable leaf')
        original = Path.stat
        def stat(path, *args, **kwargs):
            if path in blocked:
                raise PermissionError('synthetic global metadata denial')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'stat', stat):
            report, chain, graph, rows = self.analyze(self.root)
        self.assertIsNone(chain['global_source']['path'])
        self.assertIsNone(chain['global_source']['original_bytes'])
        self.assertEqual(chain['global_source']['state'], 'cache_unknown')
        self.assertEqual(chain['project_original_bytes'], source.stat().st_size)
        row = next(r for r in rows if r['terminal_path'] == str(leaf))
        self.assertEqual(row['route_original_bytes'], source.stat().st_size + leaf.stat().st_size)
        self.assertTrue(row['lower_bound'])

    def test_confirmed_absence_and_unknown_delivery_controls(self):
        self.put(self.root / 'AGENTS.md', 'Read [leaf](leaf.md).\n')
        leaf = self.put(self.root / 'leaf.md', 'readable leaf')
        for trust in ('trusted', 'unknown'):
            with self.subTest(trust=trust):
                report, chain, graph, rows = self.analyze(self.root, trust)
                self.assertEqual(chain['global_source']['state'], 'absent')
                self.assertEqual(chain['global_source']['original_bytes'], 0)
                self.assertIsInstance(chain['project_original_bytes'], int)
                if trust == 'unknown':
                    self.assertIsNone(chain['project_included_bytes'])
                    self.assertTrue(report['partial'])
                row = next(r for r in rows if r['terminal_path'] == str(leaf))
                self.assertFalse(row['lower_bound'])


class DirectoryValidationIntegration(unittest.TestCase):
    setUp = reference_fixtures.ReferenceTests.setUp
    put = reference_fixtures.ReferenceTests.put

    def run_case(self, label, failure=None):
        self.put(self.source, 'Read [docs](docs/) before editing.\n')
        changing = self.put(self.root / 'docs/changing.md', 'Read [old](../old.md).\n')
        good = self.put(self.root / 'docs/good.md', 'Sure! Follow the guide.\n')
        old = self.put(self.root / 'old.md', 'old snapshot')
        original = _Content.read
        visits = {}
        def read(content, path):
            visits[str(path)] = visits.get(str(path), 0) + 1
            if failure is not None and path == changing and visits[str(path)] >= 2:
                raise failure
            return original(content, path)
        out = self.base / label
        with patch.object(_Content, 'read', read):
            code = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                                    '--codex-home', str(self.home), '--out', str(out)])
        report = json.loads((out / 'audit.json').read_text())
        routes = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
        return code, report, routes, changing, good, old

    def test_late_read_failures_refresh_exported_directory_summaries(self):
        cases = ((OSError('file changed during scan'), 'changed_during_read'),
                 (FileNotFoundError('gone'), 'blocked_frontier'),
                 (PermissionError('denied'), 'blocked_frontier'))
        for index, (failure, kind) in enumerate(cases):
            with self.subTest(failure=type(failure).__name__):
                code, report, routes, changing, good, old = self.run_case('failed-' + str(index), failure)
                self.assertEqual(code, 3)
                self.assertTrue(report['partial'])
                self.assertTrue(any(c['path'] == str(good) for c in report['candidates']))
                self.assertTrue(any(r['terminal_path'] == str(changing) and r['terminal_kind'] == kind for r in routes))
                scenario = report['chains'][0]['scenario_id']
                docs = str(changing.parent)
                for container in (report['graph'], report['reading_summary']):
                    for row in (container['directory_summaries'][docs],
                                container['directory_summaries_by_scenario'][scenario][docs]):
                        self.assertEqual(row['frontier_counts'], {kind: 1})
                        self.assertTrue(row['lower_bound'])
                        self.assertEqual(row['physical_text_files'], 2)
                        self.assertEqual(row['unique_text_bytes'], changing.stat().st_size + good.stat().st_size)
                        self.assertTrue(any(f['path'] == str(changing) and f['kind'] == kind for f in row['frontiers']))
                        self.assertFalse(any(c['source'] == str(changing) for c in row['read_conditions']))
                        self.assertTrue(any(c['source'] == str(self.source) and 'before editing' in c['condition']
                                            for c in row['read_conditions']))
                    self.assertEqual(container['directory_totals'][docs], changing.stat().st_size + good.stat().st_size)

    def test_healthy_directory_validation_control(self):
        code, report, routes, changing, good, old = self.run_case('healthy')
        self.assertIn(code, (0, 1))
        scenario = report['chains'][0]['scenario_id']
        docs = str(changing.parent)
        for container in (report['graph'], report['reading_summary']):
            for row in (container['directory_summaries'][docs],
                        container['directory_summaries_by_scenario'][scenario][docs]):
                self.assertEqual(row['physical_text_files'], 3)
                self.assertEqual(row['unique_text_bytes'], sum(p.stat().st_size for p in (changing, good, old)))
                self.assertFalse(row['lower_bound'])
                self.assertEqual(row['frontier_counts'], {})
                self.assertTrue(any(c['source'] == str(changing) for c in row['read_conditions']))
