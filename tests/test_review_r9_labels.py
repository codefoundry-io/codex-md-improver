"""Equivalent Markdown labels preserve the first accepted definition."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_review_r8_definitions as fixtures


class NormalizedLabels(unittest.TestCase):
    setUp = fixtures.DefinitionPrecedence.setUp
    put = fixtures.DefinitionPrecedence.put
    chain = fixtures.DefinitionPrecedence.chain
    build = fixtures.DefinitionPrecedence.build
    routes = fixtures.DefinitionPrecedence.routes
    tree = fixtures.DefinitionPrecedence.tree
    check_required = fixtures.DefinitionPrecedence.check_required

    def test_equivalent_labels_choose_first_for_all_reference_forms(self):
        self.tree()
        for definition in ('build  rules', ' BUILD\tRules ', 'build\nrules', 'build\r\nrules'):
            for use in ('[policy][build rules]', '[build rules][]', '[build rules]'):
                with self.subTest(definition=definition, use=use):
                    self.put(self.source, f'Read {use}.\n\n[{definition}]: required.md\n'
                                          '[build rules]: decoy.md\n')
                    self.check_required(self.build())

    def test_use_whitespace_is_normalized_too(self):
        self.tree()
        for use in ('[policy][ BUILD\t rules ]', '[build\nrules][]', '[ build  rules ]'):
            with self.subTest(use=use):
                self.put(self.source, f'Read {use}.\n\n[build rules]: required.md\n')
                self.check_required(self.build())

    def test_missing_first_equivalent_definition_stays_partial(self):
        self.tree()
        self.required.unlink()
        self.put(self.source, 'Read [policy][build rules].\n\n[build  rules]: required.md\n'
                              '[build rules]: decoy.md\n')
        graph = self.build()
        self.assertTrue(graph['partial'])
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(self.required), 'missing_target')])

    def test_punctuation_and_unicode_space_remain_distinct(self):
        self.tree()
        self.put(self.source, 'Read [build rules].\n\n[build-rules]: decoy.md\n'
                              '[build\u00a0rules]: decoy.md\n[build rules]: required.md\n')
        self.check_required(self.build())

    def test_whitespace_only_labels_do_not_create_dependencies(self):
        self.tree()
        self.put(self.source, 'Read [ \t ].\n\n[ \t ]: decoy.md\n')
        graph = self.build()
        self.assertEqual(graph['occurrences'], [])
