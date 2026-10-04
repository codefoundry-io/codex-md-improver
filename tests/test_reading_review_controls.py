"""Global/project loader disclosure and existing heading-veto controls."""
import unittest

import test_link_table_regression as graph_fixtures
import reading_report_fixtures as report_fixtures
from test_reading_evidence import tables
from reporting import render_audit


class LoaderColumns(unittest.TestCase):
    setUp = report_fixtures.ReadingReportRegressionTests.setUp
    chain = report_fixtures.ReadingReportRegressionTests.chain
    report = report_fixtures.ReadingReportRegressionTests.report

    def test_global_and_project_loader_values_have_distinct_columns(self):
        self.source.write_text('Root instructions\n', encoding='utf-8')
        for global_values in ({'original_bytes': 43, 'included_bytes': 41},
                              {'original_bytes': 0, 'included_bytes': 0},
                              {'original_bytes': None, 'included_bytes': None}):
            with self.subTest(global_values=global_values):
                chain = self.chain('s', 113)
                report = self.report([chain])
                chain['global_source'] = global_values
                report['chains'] = [chain]
                rows = tables(render_audit(report))
                matches = [row for row in rows if 'Project loader original bytes' in row]
                self.assertEqual(len(matches), 1)
                row = matches[0]
                self.assertEqual(row['Project loader original bytes'], str(chain['project_original_bytes']))
                self.assertEqual(row['Project loader included bytes'], '113')
                for label, key in (('Global loader original bytes', 'original_bytes'),
                                   ('Global loader included bytes', 'included_bytes')):
                    self.assertEqual(row[label], 'unknown' if global_values[key] is None else str(global_values[key]))


class ReadingHeadingControls(unittest.TestCase):
    setUp = graph_fixtures.LinkTableRegressionTests.setUp
    put = graph_fixtures.LinkTableRegressionTests.put
    chain = graph_fixtures.LinkTableRegressionTests.chain
    build = graph_fixtures.LinkTableRegressionTests.build

    def test_read_headings_atx_closing_hashes_and_setext_equals_promote(self):
        for heading in ('## Read before editing ##\n', 'Read before editing\n===================\n'):
            with self.subTest(heading=heading):
                self.put('AGENTS.md', heading + '\n| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n')
                guide = self.put('guide.md', 'required\n')
                edge, = self.build()['occurrences']
                self.assertEqual(edge['classification'], 'read_dependency')
                self.assertEqual(edge['targets'], [str(guide)])

    def test_read_load_output_example_and_mixed_heading_veto_remains(self):
        for heading in ('Load example outputs', 'Read before you write', 'Read sample output'):
            with self.subTest(heading=heading):
                self.put('AGENTS.md', '## ' + heading + '\n\n| Operation | Reference |\n|---|---|\n| Build | `guide.md` |\n')
                self.put('guide.md', 'not required by this heading\n')
                graph = self.build()
                edge, = graph['occurrences']
                self.assertEqual(edge['classification'], 'uncertain')
                self.assertEqual(len(graph['nodes']), 1)


if __name__ == '__main__':
    unittest.main()
