"""Literal expansion prefixes and reference-definition title regressions."""
import unittest
import test_references as fixtures


class ReferenceExpansionReview(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def test_expanded_paths_keep_literal_prefixes_for_files_and_globs(self):
        renamed = self.root.parent / '[archive]'
        self.root.rename(renamed)
        self.root, self.source = renamed, renamed / 'AGENTS.md'
        intended = self.put(self.root / 'docs/a.md', 'intended guide')
        decoy = self.put(self.root.parent / 'a/docs/a.md', 'wrong sibling')
        for prefix in ('${PROJECT_ROOT}', '${CWD}', '$HOME', '$CODEX_HOME', '~'):
            for leaf in ('a.md', '*.md'):
                with self.subTest(prefix=prefix, leaf=leaf):
                    self.put(self.source, '[guide](' + prefix + '/docs/' + leaf + ')\n')
                    graph = self.build(user_home=self.root, codex_home=self.root)
                    terminals = {r['terminal_path'] for r in self.routes(graph)}
                    self.assertIn(str(intended), terminals)
                    self.assertNotIn(str(decoy), terminals)
                    self.assertFalse(graph['partial'])

    def test_angle_destination_occupies_its_entire_titled_definition(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        for title in ('"other.md"', "'other.md'", '(other.md)'):
            for use in ('[guide][g]', '[g]'):
                with self.subTest(title=title, use=use):
                    self.put(self.source, 'Read ' + use + '.\n[g]: <guide.md> ' + title + '\n')
                    graph = self.build()
                    self.assertFalse(graph['partial'])
                    self.assertEqual([e['target_text'] for e in graph['occurrences']], ['guide.md'])
                    self.assertEqual({r['terminal_path'] for r in self.routes(graph)}, {str(guide)})

    def test_next_line_destinations_retain_reference_routes_and_title_exclusion(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        for destination in ('guide.md', '<guide.md>'):
            for use in ('[guide][g]', '[g]'):
                with self.subTest(destination=destination, use=use):
                    self.put(self.source, 'Read ' + use + '.\n[g]:\n  ' + destination + ' "other.md"\n')
                    graph = self.build()
                    self.assertFalse(graph['partial'])
                    self.assertEqual([e['target_text'] for e in graph['occurrences']], ['guide.md'])
                    self.assertEqual({r['terminal_path'] for r in self.routes(graph)}, {str(guide)})


if __name__ == '__main__':
    unittest.main()
