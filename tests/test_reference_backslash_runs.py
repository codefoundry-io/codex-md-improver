"""GFM escaped pipes stay inside cells after any backslash run."""
import unittest
import test_link_table_regression as fixtures


class ReferenceBackslashRuns(unittest.TestCase):
    setUp = fixtures.LinkTableRegressionTests.setUp
    put = fixtures.LinkTableRegressionTests.put
    chain = fixtures.LinkTableRegressionTests.chain
    build = fixtures.LinkTableRegressionTests.build

    def test_operation_escaped_pipe_runs_do_not_shift_reference_column(self):
        for count in (1, 2, 3, 4):
            with self.subTest(backslashes=count):
                prefix = 'Alpha' + '\\' * count + '|Beta '
                self.put('AGENTS.md', '## Load for the current operation\n\n'
                         '| Operation | Reference |\n|---|---|\n'
                         f'| {prefix}`operation.md` | `guide.md` |\n')
                self.put('operation.md', 'operation text only\n')
                guide = self.put('guide.md', 'required reference\n')
                graph = self.build()
                edges = {edge['target_text']: edge for edge in graph['occurrences']}
                self.assertEqual(edges['operation.md']['classification'], 'uncertain')
                self.assertEqual(edges['operation.md']['targets'], [])
                self.assertEqual(edges['guide.md']['classification'], 'read_dependency')
                self.assertEqual(edges['guide.md']['targets'], [str(guide)])
                self.assertEqual(len(graph['nodes']), 2)

    def test_header_escaped_pipe_runs_preserve_reference_column(self):
        for count in (1, 2, 3, 4):
            with self.subTest(backslashes=count):
                heading = 'Operation' + '\\' * count + '|Detail'
                self.put('AGENTS.md', '## Load for the current operation\n\n'
                         f'| {heading} | Reference |\n|---|---|\n| Build | `guide.md` |\n')
                guide = self.put('guide.md', 'required reference\n')
                edge, = self.build()['occurrences']
                self.assertEqual(edge['classification'], 'read_dependency')
                self.assertEqual(edge['targets'], [str(guide)])


if __name__ == '__main__':
    unittest.main()
