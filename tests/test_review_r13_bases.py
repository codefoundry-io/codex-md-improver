"""R13 CLI validation of every declared reference base, including unused aliases."""
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures


class DeclaredBaseValidation(unittest.TestCase):
    # Delegate helpers only: no inherited fixture tests. setUp honors CODEX_MD_TEST_TMP.
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    cli = fixtures.ReferenceTests.cli

    def scan_bases(self, bases):
        settings = self.put(self.base / 'settings.json',
                            json.dumps({'schema_version': 1, 'declared_bases': bases}))
        return self.cli(['--settings', str(settings)])

    def assert_invalid(self, bases):
        # The default AGENTS.md has no links; every declaration here is unused.
        result, out = self.scan_bases(bases)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('Audit input/output error:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(out.exists(), 'Invalid input must fail before output creation')

    def assert_accepted(self, bases):
        result, out = self.scan_bases(bases)
        self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        audit = json.loads((out / 'audit.json').read_text())
        self.assertFalse(audit['partial'])
        self.assertTrue(any(chain['sources'] for chain in audit['chains']))
        return out, audit

    def test_unused_nonobject_base_records_are_rejected(self):
        alias = str(self.base / 'unused/AGENTS.md')
        for record in (None, [], 'document_dir', 7, True):
            with self.subTest(record=record):
                self.assert_invalid({alias: record})

    def test_unused_missing_unknown_and_nonstring_kinds_are_rejected(self):
        alias = str(self.base / 'unused/AGENTS.md')
        records = ({}, {'kind': 'unknown'}, {'kind': None}, {'kind': 7},
                   {'kind': True}, {'kind': []}, {'kind': {}})
        for record in records:
            with self.subTest(record=record):
                self.assert_invalid({alias: record})

    def test_unused_base_records_reject_extra_fields_for_all_kinds(self):
        alias = str(self.base / 'unused/AGENTS.md')
        for kind in ('document_dir', 'scenario_project_root', 'scenario_cwd', 'absolute'):
            record = {'kind': kind, 'extra': 'not allowed'}
            if kind == 'absolute':
                record['path'] = str(self.base / 'nonexistent-base')
            with self.subTest(kind=kind):
                self.assert_invalid({alias: record})
            if kind != 'absolute':
                with self.subTest(kind=kind, field='path'):
                    self.assert_invalid({alias: {'kind': kind,
                                                'path': str(self.base / 'also-not-allowed')}})

    def test_unused_absolute_bases_require_an_absolute_string_path(self):
        alias = str(self.base / 'unused/AGENTS.md')
        records = ({'kind': 'absolute'}, {'kind': 'absolute', 'path': 'relative/base'},
                   {'kind': 'absolute', 'path': ''}, {'kind': 'absolute', 'path': None},
                   {'kind': 'absolute', 'path': 7}, {'kind': 'absolute', 'path': []})
        for record in records:
            with self.subTest(record=record):
                self.assert_invalid({alias: record})

    def test_relative_source_alias_keys_are_rejected(self):
        # JSON object keys are strings; relative and empty strings reach the CLI unchanged.
        for alias in ('AGENTS.md', './unused/AGENTS.md', ''):
            with self.subTest(alias=alias):
                self.assert_invalid({alias: {'kind': 'document_dir'}})

    def test_all_four_exact_base_shapes_accept_unmatched_absolute_aliases(self):
        # Alias matching, existence and dot-dot normalization are not schema requirements.
        alias = str(self.base / 'missing/../unused/AGENTS.md')
        missing_base = str(self.base / 'missing/../nonexistent-base')
        self.assertFalse(Path(alias).exists())
        self.assertFalse(Path(missing_base).exists())
        records = ({'kind': 'document_dir'}, {'kind': 'scenario_project_root'},
                   {'kind': 'scenario_cwd'}, {'kind': 'absolute', 'path': missing_base})
        for record in records:
            with self.subTest(record=record):
                self.assert_accepted({alias: record})

    def test_matched_document_base_still_resolves_relative_target(self):
        leaf = self.put(self.root / 'docs/leaf.md', 'Leaf instructions.\n')
        self.put(self.source, 'Read `docs/leaf.md` before editing.\n')
        out, audit = self.assert_accepted({str(self.source): {'kind': 'document_dir'}})
        self.assertTrue(audit['text_read_complete'])
        routes = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
        self.assertTrue(any(row['terminal_path'] == str(leaf) and row['terminal_kind'] == 'leaf'
                            for row in routes))


if __name__ == '__main__':
    unittest.main()
