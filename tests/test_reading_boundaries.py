"""Excluded-skill status and bounded renderer/heading controls from R3."""
import copy
import unittest
import test_link_table_regression as links
import reading_report_fixtures as fixtures
from test_reading_evidence import tables
from reporting import render_audit


class ReadingBoundaryTests(unittest.TestCase):
    setUp = fixtures.ReadingReportRegressionTests.setUp
    put = fixtures.ReadingReportRegressionTests.put
    source_text = fixtures.ReadingReportRegressionTests.source_text
    chain = fixtures.ReadingReportRegressionTests.chain
    report = fixtures.ReadingReportRegressionTests.report

    def persisted(self, report):
        report['graph'] = {key: value for key, value in report['graph'].items()
                           if not key.startswith('_')}
        return report

    def test_excluded_skill_is_visible_lower_bound_without_changing_coverage(self):
        for target in ('docs/', 'docs/skill/SKILL.md'):
            with self.subTest(target=target):
                self.source_text(f'[tree]({target})\n')
                self.put('docs/skill/SKILL.md', 'excluded instructions\n')
                self.put('docs/skill/hidden.md', 'excluded sibling\n')
                self.put('docs/readable.md', 'readable')
                report = self.persisted(self.report([self.chain('boundary')]))
                states = report['graph']['states'].values()
                self.assertTrue(any(state['kind'] == 'excluded_skill' for state in states))
                self.assertFalse(report['graph']['partial'])
                self.assertTrue(report['graph']['text_read_complete'])
                self.assertEqual(report['reading_summary']['unique_text_bytes'],
                                 145 if target == 'docs/' else 137)
                before = copy.deepcopy(report)
                rendered = render_audit(report)
                rows = tables(rendered)
                metric = [row for row in rows if row.get('Metric') == 'Known unique reachable text bytes']
                self.assertEqual(len(metric), 1)
                self.assertEqual(metric[0]['Status'], 'lower bound')
                excluded = [row for row in rows if row.get('Limited kind') == 'excluded_skill']
                self.assertEqual(len(excluded), 1)
                self.assertEqual(excluded[0]['Scenario state count'], '1')
                self.assertIn('intentional boundary', rendered.lower())
                self.assertIn('Coverage: declared area complete.', rendered)
                self.assertEqual(report, before)

    def test_public_graph_cells_preserve_markdown_and_adjacent_escapes_literally(self):
        self.source_text('Read `unknown.md`.\n')
        cwd = self.root / 'nested'
        cwd.mkdir()
        report = self.persisted(self.report([self.chain('cells', cwd=cwd)]))
        edge, = report['graph']['occurrences']
        self.assertEqual(edge['status'], 'unresolved')
        hostile = r'Follow [common](docs/common.md) **bold** _italics_ https://example.invalid/a \\| literal\r tail' + '\\'
        edge['condition'] = hostile
        before = copy.deepcopy(report)
        rendered = render_audit(report)
        rows = tables(rendered)
        matching = [row for row in rows if row.get('Target') == 'unknown.md']
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]['Condition'], hostile)
        # Encoded punctuation cannot become links/emphasis/autolinks in Markdown.
        self.assertNotIn('[common](', rendered)
        self.assertNotIn('**bold**', rendered)
        self.assertNotIn('_italics_', rendered)
        self.assertNotIn('https://example.invalid/a', rendered)
        self.assertEqual(report, before)


class HeadingProseControls(unittest.TestCase):
    setUp = links.LinkTableRegressionTests.setUp
    put = links.LinkTableRegressionTests.put
    chain = links.LinkTableRegressionTests.chain
    build = links.LinkTableRegressionTests.build

    def test_Load_heading_does_not_promote_non_table_prose_or_list_paths(self):
        self.put('AGENTS.md', '## Load for the operation\n\nThe archive lives at `old/notes.md`.\n- Backup location: `old/backup.md`.\n')
        self.put('old/notes.md', 'archive')
        self.put('old/backup.md', 'backup')
        graph = self.build()
        self.assertEqual([edge['classification'] for edge in graph['occurrences']],
                         ['uncertain', 'uncertain'])
        self.assertEqual(len(graph['nodes']), 1)


if __name__ == '__main__':
    unittest.main()
