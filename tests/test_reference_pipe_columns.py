"""Column identity and actual table delimiter controls for the new fallback."""
import unittest
import test_link_table_regression as fixtures


class ReferencePipeColumns(unittest.TestCase):
    setUp = fixtures.LinkTableRegressionTests.setUp
    put = fixtures.LinkTableRegressionTests.put
    chain = fixtures.LinkTableRegressionTests.chain
    build = fixtures.LinkTableRegressionTests.build

    def test_escaped_pipe_does_not_move_operation_path_into_Reference(self):
        for prefix in ('Alpha\\|Beta ', 'Alpha '):
            with self.subTest(prefix=prefix):
                self.put('AGENTS.md', '## Load for the current operation\n\n'
                         '| Operation | Reference |\n|---|---|\n'
                         f'| {prefix}`operation.md` | `guide.md` |\n')
                self.put('operation.md', 'not required by this column\n')
                guide = self.put('guide.md', 'required by Reference\n')
                graph = self.build()
                edges = {edge['target_text']: edge for edge in graph['occurrences']}
                self.assertEqual(edges['operation.md']['classification'], 'uncertain')
                self.assertEqual(edges['operation.md']['targets'], [])
                self.assertEqual(edges['guide.md']['classification'], 'read_dependency')
                self.assertEqual(edges['guide.md']['targets'], [str(guide)])
                self.assertEqual(len(graph['nodes']), 2)

    def test_missing_or_mismatched_delimiter_does_not_declare_Reference_table(self):
        for delimiter in ('', '|---|\n', '|notes|details|\n'):
            with self.subTest(delimiter=delimiter):
                self.put('AGENTS.md', '## Load for the current operation\n\n'
                         '| Operation | Reference |\n' + delimiter + '| Build | `guide.md` |\n')
                self.put('guide.md', 'not a declared table read\n')
                graph = self.build()
                edge, = graph['occurrences']
                self.assertEqual(edge['classification'], 'uncertain')
                self.assertEqual(len(graph['nodes']), 1)


if __name__ == '__main__':
    unittest.main()
