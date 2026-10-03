"""R4 inline delimiter and URL punctuation regressions."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures


class InlineDelimiterReview(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def test_parentheses_in_destinations_survive_optional_titles(self):
        for filename in ('guide(1).md', 'guide((1)).md'):
            guide = self.put(self.root / filename, 'guide')
            for destination in (filename, '<' + filename + '>'):
                for title in ('', ' "Guide title"', " 'Guide title'", ' (Guide title)'):
                    with self.subTest(filename=filename, destination=destination, title=title):
                        text = 'Read [guide](' + destination + title + ').\n'
                        self.put(self.source, text)
                        graph = self.build()
                        self.assertEqual([e['target_text'] for e in graph['occurrences']], [filename])
                        self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})
                        self.assertFalse(graph['partial'])
                        start, end = graph['occurrences'][0]['span']
                        self.assertEqual(text[start:end], filename)

    def test_title_closers_and_quoted_paths_stay_outside_dependencies(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        fake = self.put(self.root / 'fake.md', 'title decoy')
        for title in ('"see ) fake.md"', "'see ) fake.md'", '(see \\) fake.md)',
                      '"see ) `fake.md`"'):
            with self.subTest(title=title):
                self.put(self.source, 'Read [guide](guide.md ' + title + ').\n')
                graph = self.build()
                self.assertEqual([e['target_text'] for e in graph['occurrences']], ['guide.md'])
                paths = {r['terminal_path'] for r in self.routes(graph)}
                self.assertIn(str(guide), paths)
                self.assertNotIn(str(fake), paths)
                self.assertFalse(graph['partial'])

    def test_balanced_url_punctuation_is_preserved(self):
        url = 'https://example.com/Function_(mathematics)'
        for text in ('Read ' + url, 'Read ' + url + '.', 'See (' + url + ').'):
            with self.subTest(text=text):
                self.put(self.source, text + '\n')
                graph = self.build()
                self.assertEqual([e['target_text'] for e in graph['occurrences']], [url])
                self.assertEqual(graph['occurrences'][0]['status'], 'url')
                self.assertFalse(graph['partial'])

    def test_title_words_do_not_change_explicit_read_intent(self):
        guide = self.put(self.root / 'guide.md', 'guide')
        for word in ('output', 'example', 'create', 'sample'):
            with self.subTest(word=word):
                self.put(self.source, 'Read [guide](guide.md "see ) ' + word + '.md").\n')
                graph = self.build()
                self.assertEqual(graph['occurrences'][0]['classification'], 'read_dependency')
                self.assertFalse(graph['partial'])
                self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})
