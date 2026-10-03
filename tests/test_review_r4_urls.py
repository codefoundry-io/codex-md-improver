"""URL inventory invariants and Unicode-path semantic-resolution controls."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures


class UrlInventoryReview(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    decision = fixtures.ReferenceTests.decision

    def test_plain_and_autolink_urls_never_invent_local_paths(self):
        for text, expected in (
            ('Read the docs at https://platform.openai.com/docs/.', 'https://platform.openai.com/docs/'),
            ('Docs: https://developers.openai.com/codex', 'https://developers.openai.com/codex'),
            ('<https://example.com/a>', 'https://example.com/a'),
            ('Example: <mailto:help@example.com>', 'mailto:help@example.com'),
        ):
            with self.subTest(text=text):
                self.put(self.source, text + '\n')
                graph = self.build()
                self.assertEqual([e['target_text'] for e in graph['occurrences']], [expected])
                self.assertEqual(graph['occurrences'][0]['status'], 'url')
                self.assertFalse(graph['partial'])
                self.assertFalse(any(r['terminal_kind'] == 'missing_target' for r in self.routes(graph)))

    def test_nonlocal_targets_bypass_ambiguous_read_classification(self):
        for prefix in ('Example:', 'Create PRs per', 'Read and output'):
            for target, status in (('https://example.com/guide.md', 'url'),
                                   ('tel:123', 'url'), ('#section', 'self_reference')):
                with self.subTest(prefix=prefix, target=target):
                    self.put(self.source, prefix + ' [guide](' + target + ').\n')
                    graph = self.build()
                    self.assertEqual(graph['occurrences'][0]['status'], status)
                    self.assertFalse(graph['partial'])
                    self.assertFalse(any(r['terminal_kind'] == 'missing_target' for r in self.routes(graph)))

    def test_local_ambiguity_and_existing_markdown_uri_controls(self):
        self.put(self.root / 'guide.md', 'guide')
        self.put(self.source, 'Example: [guide](guide.md)\n')
        graph = self.build()
        self.assertTrue(graph['partial'])
        self.assertEqual(graph['occurrences'][0]['status'], 'unresolved')
        self.put(self.source, '[guide](https://example.com/guide.md)\n')
        graph = self.build()
        self.assertEqual(len(graph['occurrences']), 1)
        self.assertEqual(graph['occurrences'][0]['status'], 'url')
        self.assertFalse(graph['partial'])

    def test_unicode_extension_and_particle_resolution_control(self):
        intended = self.put(self.root / 'docs/guide.md', 'intended document')
        text = 'docs/guide.md를 먼저 읽을 것\n'
        self.put(self.source, text)
        graph = self.build()
        self.assertTrue(graph['partial'])
        resolution = self.decision('docs/guide.md를', target='docs/guide.md', base={'kind': 'document_dir'})
        graph = self.build(resolutions=[resolution])
        self.assertFalse(graph['partial'])
        self.assertIn(str(intended), {r['terminal_path'] for r in self.routes(graph)})
        exact = self.put(self.root / 'docs/guide.md를', 'legitimate Unicode extension')
        self.put(self.source, 'Read docs/guide.md를.\n')
        graph = self.build()
        self.assertFalse(graph['partial'])
        self.assertIn(str(exact), {r['terminal_path'] for r in self.routes(graph)})
        self.assertNotIn(str(intended), {r['terminal_path'] for r in self.routes(graph)})
