"""Native stored spelling controls excluded skill and Git boundaries."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as reference_fixtures
import test_reporting as reporting_fixtures
from discovery import _Content, _POLICY
from reporting import enrich_audit
import md_improver


class NativeExcludedReferences(unittest.TestCase):
    setUp = reference_fixtures.ReferenceTests.setUp
    put = reference_fixtures.ReferenceTests.put
    chain = reference_fixtures.ReferenceTests.chain
    build = reference_fixtures.ReferenceTests.build
    routes = reference_fixtures.ReferenceTests.routes

    def check_boundary(self, stored_name, alias_name, expected):
        stored = self.put(self.root / stored_name, 'Sure! Read [nested](nested.md).\n')
        alias = self.root / alias_name
        if not alias.exists():
            self.skipTest('fixture volume is case-sensitive; native alias does not exist')
        self.assertTrue(stored.samefile(alias))
        self.put(stored.parent / 'nested.md', 'Nested content must remain outside the audit.')
        self.put(self.source, f'Read [boundary]({alias_name}).\n')
        excluded_id = (stored.stat().st_dev, stored.stat().st_ino)
        reads = []
        original = Path.read_bytes
        def track(path):
            info = path.stat()
            if (info.st_dev, info.st_ino) == excluded_id:
                reads.append(str(path))
            return original(path)
        content = _Content()
        with patch.object(Path, 'read_bytes', track):
            graph = self.build(content=content)
            candidates = md_improver._candidate_records(graph, self.chains, content, set(_POLICY['detector_ids']))
        self.assertEqual(reads, [], 'Excluded physical file was read through a case alias')
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(alias), expected)])
        self.assertFalse(any(str(alias) in n['aliases'] for n in graph['nodes'].values()))
        self.assertFalse(any(c['path'] == str(alias) for c in candidates))
        self.assertFalse(any(e['source'] == str(alias) for e in graph['occurrences']))

    def test_native_skill_case_alias_is_metadata_only(self):
        self.check_boundary('deploy/SKILL.md', 'deploy/skill.md', 'excluded_skill')

    def test_native_git_case_alias_is_metadata_only(self):
        self.check_boundary('.git/config', '.GIT/config', 'excluded_git')

    def test_actually_lowercase_skill_filename_remains_regular_reference(self):
        leaf = self.put(self.root / 'ordinary/skill.md', 'Ordinary lowercase document.')
        self.put(self.source, 'Read [ordinary](ordinary/skill.md).\n')
        graph = self.build()
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(leaf), 'leaf')])
        self.assertFalse(graph['partial'])


class NativeExcludedAssessment(unittest.TestCase):
    setUp = reporting_fixtures.ReportingTests.setUp
    make_audit = reporting_fixtures.ReportingTests.make_audit
    evidence = reporting_fixtures.ReportingTests.evidence
    assessment = reporting_fixtures.ReportingTests.assessment
    finding = reporting_fixtures.ReportingTests.finding

    def check_exclusion(self, stored_name, alias_name):
        stored = self.project / stored_name
        stored.parent.mkdir(parents=True, exist_ok=True)
        stored.write_text('α Require approval.\nKeep scope narrow.\n')
        self.source = self.project / alias_name
        if not self.source.exists():
            self.skipTest('fixture volume is case-sensitive; native alias does not exist')
        self.assertTrue(stored.samefile(self.source))
        self.audit = self.make_audit()
        assessment = self.assessment(findings=[self.finding()])
        original = _Content.read
        reads = []
        def track(content, path):
            reads.append(str(path))
            return original(content, path)
        with patch.object(_Content, 'read', track):
            with self.assertRaisesRegex(ValueError, 'excluded source'):
                enrich_audit(self.audit, assessment)
        self.assertEqual(reads, [], 'Assessment read an excluded source')

    def test_native_skill_case_alias_assessment_rejects_before_read(self):
        self.check_exclusion('deploy/SKILL.md', 'deploy/skill.md')

    def test_native_git_case_alias_assessment_rejects_before_read(self):
        self.check_exclusion('.git/config', '.GIT/config')
