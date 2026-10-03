"""R14 optional resolution bases obey the exact reference-base input schema."""
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures


class ResolutionBaseValidation(unittest.TestCase):
    # Helper delegation avoids inherited tests; setUp honors CODEX_MD_TEST_TMP.
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    decision = fixtures.ReferenceTests.decision
    cli = fixtures.ReferenceTests.cli

    def scan_decision(self, text, base, classification='read_dependency'):
        self.put(self.source, 'Read [guide](' + text + ') before editing.\n')
        row = self.decision(text, classification, base=base)
        path = self.put(self.base / 'resolutions.json', json.dumps([row]))
        return self.cli(['--resolutions', str(path)])

    def assert_invalid(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('Audit input/output error:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        # The contract specifies exit 2, not whether an output directory exists.

    def test_empty_relative_base_is_invalid_instead_of_defaulted(self):
        self.put(self.root / 'guide.md', 'Guide instructions.\n')
        result, _ = self.scan_decision('guide.md', {})
        self.assert_invalid(result)

    def test_malformed_bases_are_invalid_even_when_traversal_bypasses_base(self):
        leaf = self.put(self.root / 'guide.md', 'Guide instructions.\n')
        malformed = ({}, None, [], {'kind': []}, {'kind': 'unknown'},
                     {'kind': 'document_dir', 'extra': True}, {'kind': 'absolute'},
                     {'kind': 'absolute', 'path': 'relative/base'})
        for mode in ('absolute_target', 'uncertain'):
            for base in malformed:
                with self.subTest(mode=mode, base=base):
                    text = str(leaf) if mode == 'absolute_target' else 'guide.md'
                    classification = 'uncertain' if mode == 'uncertain' else 'read_dependency'
                    result, _ = self.scan_decision(text, base, classification)
                    self.assert_invalid(result)

    def test_exact_base_shapes_resolve_and_valid_uncertain_remains_partial(self):
        leaf = self.put(self.root / 'guide.md', 'Guide instructions.\n')
        bases = ({'kind': 'document_dir'}, {'kind': 'scenario_project_root'},
                 {'kind': 'scenario_cwd'}, {'kind': 'absolute', 'path': str(self.root)})
        for base in bases:
            with self.subTest(base=base):
                result, out = self.scan_decision('guide.md', base)
                self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
                audit = json.loads((out / 'audit.json').read_text())
                self.assertFalse(audit['partial'])
                routes = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
                self.assertTrue(any(row['terminal_path'] == str(leaf) and row['terminal_kind'] == 'leaf'
                                    for row in routes))
        result, out = self.scan_decision('guide.md', {'kind': 'document_dir'}, 'uncertain')
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertTrue(json.loads((out / 'audit.json').read_text())['partial'])


if __name__ == '__main__':
    unittest.main()
