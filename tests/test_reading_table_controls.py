"""Bounded negative-heading and limited-terminal display controls."""
import unittest
import test_link_table_regression as links
import reading_report_fixtures as rendering
from test_reading_evidence import tables
from reporting import render_audit


class HeadingTokenControls(unittest.TestCase):
    setUp = links.LinkTableRegressionTests.setUp
    put = links.LinkTableRegressionTests.put
    chain = links.LinkTableRegressionTests.chain
    build = links.LinkTableRegressionTests.build

    def test_non_imperative_Read_Load_prefixes_do_not_traverse(self):
        for heading in ('Read-only boundaries', 'Reading conventions', 'README', 'Loading notes'):
            with self.subTest(heading=heading):
                self.put('AGENTS.md', f'## {heading}\n\n| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n')
                self.put('guide.md', 'not a required read\n')
                graph = self.build()
                self.assertEqual([(e['classification'], e['targets']) for e in graph['occurrences']],
                                 [('uncertain', [])])
                self.assertEqual(len(graph['nodes']), 1)


class LimitedReportControls(unittest.TestCase):
    setUp = rendering.ReadingReportRegressionTests.setUp
    put = rendering.ReadingReportRegressionTests.put
    source_text = rendering.ReadingReportRegressionTests.source_text
    chain = rendering.ReadingReportRegressionTests.chain
    report = rendering.ReadingReportRegressionTests.report

    def test_resolved_missing_target_has_visible_limited_kind_count(self):
        self.source_text('[missing](docs/absent.md)\n')
        report = self.report([self.chain('missing')])
        edge, = report['graph']['occurrences']
        self.assertEqual(edge['status'], 'resolved')
        self.assertTrue(report['graph']['partial'])
        self.assertFalse(any(e['status'] == 'unresolved' for e in report['graph']['occurrences']))
        states = report['graph']['states'].values()
        self.assertEqual(sum(state['kind'] == 'missing_target' for state in states), 1)
        rows = tables(render_audit(report))
        missing = [row for row in rows if row.get('Limited kind') == 'missing_target']
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['Scenario state count'], '1')


if __name__ == '__main__':
    unittest.main()
