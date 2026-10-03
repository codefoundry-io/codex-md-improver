"""Preserve numeric URI payloads while supporting documented filename line suffixes."""
import unittest
import test_references as fixtures


class NumericUriReview(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def test_port_and_numeric_opaque_uri_stay_urls(self):
        for target in ('https://example.org:443', 'tel:123', 'custom:123'):
            with self.subTest(target=target):
                self.put(self.source, '[link](' + target + ')\n')
                graph = self.build()
                self.assertFalse(graph['partial'])
                self.assertEqual(graph['occurrences'][0]['status'], 'url')
        guide = self.put(self.root / 'guide.md', 'guide')
        self.put(self.source, '[guide](guide.md:12)\n')
        graph = self.build()
        self.assertFalse(graph['partial'])
        self.assertIn(str(guide), {r['terminal_path'] for r in self.routes(graph)})


if __name__ == '__main__':
    unittest.main()
