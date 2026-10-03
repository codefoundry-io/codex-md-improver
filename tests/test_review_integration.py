"""Bounded full-review regressions against the canonical skill, no target writes."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as refs
import test_reporting as reports
from reporting import enrich_audit, compare_reports, report_hash
from discovery import _Content
import md_improver


class ReviewReferences(unittest.TestCase):
    setUp = refs.ReferenceTests.setUp
    put = refs.ReferenceTests.put
    chain = refs.ReferenceTests.chain
    build = refs.ReferenceTests.build
    routes = refs.ReferenceTests.routes

    def test_glob_denial_keeps_readable_sibling_and_partial_frontier(self):
        shared = self.base / 'shared'
        good = self.put(shared / 'readable/a.md', 'readable sibling')
        denied = self.put(shared / 'denied/b.md', 'unreadable sibling').parent
        self.put(self.source, '[guides](' + str(shared / '*/*.md') + ')\n')
        scandir = os.scandir
        def enumerate_dir(path):
            if Path(path) == denied:
                raise PermissionError('injected glob enumeration denial')
            return scandir(path)
        with patch('os.scandir', enumerate_dir):
            graph = self.build()
        rows = self.routes(graph)
        self.assertIn(str(good), {r['terminal_path'] for r in rows})
        self.assertTrue(graph['partial'])
        self.assertFalse(graph['text_read_complete'])
        self.assertTrue(any(r['terminal_kind'] in {'blocked_frontier', 'unresolved'} for r in rows))

    def test_picked_fallback_and_extensionless_instruction_follow_references(self):
        leaf = self.put(self.root / 'rules.md', 'rules')
        for name in ('INSTRUCTIONS', '.cursorrules'):
            with self.subTest(name=name):
                source = self.put(self.root / name, '[rules](rules.md)\n')
                graph = self.build([self.chain(source=source)])
                self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})
        linked = self.put(self.root / 'CONVENTIONS', '[rules](rules.md)\n')
        self.put(self.source, '[conventions](CONVENTIONS)\n')
        graph = self.build()
        self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})
        self.assertIn(str(linked), {a for n in graph['nodes'].values() for a in n['aliases']})

    def test_mixed_read_output_verbs_cannot_claim_dependency_is_nonread(self):
        self.put(self.root / 'guide.md', 'guide')
        for line in ('Read [guide](guide.md) before you write tests.',
                     'Before you create a PR, see [guide](guide.md).',
                     'Read [guide](guide.md) for an example.'):
            with self.subTest(line=line):
                self.put(self.source, line + '\n')
                graph = self.build()
                occurrence = next(e for e in graph['occurrences'] if e['target_text'] == 'guide.md')
                self.assertNotEqual(occurrence['status'], 'non_read')
                self.assertTrue(graph['partial'] or any(str(self.root / 'guide.md') in n['aliases'] for n in graph['nodes'].values()))

    def test_shortcut_reference_link_follows_defined_target(self):
        leaf = self.put(self.root / 'docs/guide.md', 'guide')
        self.put(self.source, 'See [guide] before releasing.\n\n[guide]: docs/guide.md\n')
        graph = self.build()
        self.assertIn(str(leaf), {r['terminal_path'] for r in self.routes(graph)})
        self.assertFalse(graph['partial'])

    def test_anchor_and_nonhierarchical_uri_are_not_missing_files(self):
        self.put(self.source, '[Section](#section)\n[contact](mailto:a@b.c)\n\n## Section\ntext\n')
        graph = self.build()
        self.assertFalse(graph['partial'])
        self.assertFalse(any(r['terminal_kind'] in {'missing_target', 'unresolved'} for r in self.routes(graph)))
        self.assertEqual(len(graph['occurrences']), 2)

    def test_markdown_suffix_gets_markdown_candidate_rules(self):
        self.put(self.source, '[guide](guide.markdown)\n')
        linked = self.put(self.root / 'guide.markdown', 'plain guidance\n' * 101)
        content = _Content()
        graph = self.build(content=content)
        candidates = md_improver._candidate_records(graph, self.chains, content, {'L-C9-TOC'})
        self.assertTrue(any(c['path'] == str(linked) and c['rule_id'] == 'L-C9-TOC' for c in candidates))

    def test_candidate_read_failure_keeps_routes_and_usable_siblings(self):
        self.put(self.source, '[changing](changing.md)\n[good](good.md)\n')
        changed = self.put(self.root / 'changing.md', 'changing text')
        good = self.put(self.root / 'good.md', 'Sure! Follow the guide.')
        original_read = _Content.read
        for index, failure in enumerate((OSError('file changed during scan'), FileNotFoundError('gone'), PermissionError('denied'))):
            with self.subTest(failure=type(failure).__name__):
                visits = {}
                def read(content, path):
                    visits[str(path)] = visits.get(str(path), 0) + 1
                    if path == changed and visits[str(path)] >= 2:
                        raise failure
                    return original_read(content, path)
                out = self.base / ('candidate-' + str(index))
                with patch.object(_Content, 'read', read):
                    result = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                                              '--codex-home', str(self.home), '--out', str(out)])
                self.assertEqual(result, 3)
                report = json.loads((out / 'audit.json').read_text())
                self.assertTrue(report['partial'])
                self.assertFalse(report['text_read_complete'])
                self.assertTrue(any(c['path'] == str(good) for c in report['candidates']))
                rows = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
                self.assertTrue(any(r['terminal_path'] == str(good) for r in rows))
                self.assertTrue(any(r['terminal_path'] == str(changed) and r['terminal_kind'] in {'changed_during_read', 'blocked_frontier', 'missing_target'} for r in rows))


class ReviewComparison(unittest.TestCase):
    setUp = reports.ReportingTests.setUp
    make_audit = reports.ReportingTests.make_audit
    evidence = reports.ReportingTests.evidence
    assessment = reports.ReportingTests.assessment
    finding = reports.ReportingTests.finding

    def test_unread_after_source_cannot_be_covered_by_a_path_claim(self):
        before = enrich_audit(self.audit, self.assessment(findings=[self.finding()]))
        original = self.source
        self.source = self.project / 'other.md'
        self.source.write_text('Require approval.\n')
        audit = self.make_audit()
        after = enrich_audit(audit, self.assessment(audit, resolves=[{
            'before_report_sha256': report_hash(before), 'before_finding_id': 'issue',
            'evidence': [self.evidence()], 'reason': 'claimed repair'}]))
        after['reviewed_sources'].append(str(original))
        original.unlink()  # Comparison must use snapshots, never reread this historical source.
        with self.assertRaises(ValueError):
            compare_reports(before, after)

    def test_duplicate_persisted_reviewed_source_is_rejected(self):
        report = enrich_audit(self.audit, self.assessment())
        report['reviewed_sources'] *= 2
        with self.assertRaises(ValueError):
            compare_reports(report, report)


if __name__ == '__main__':
    unittest.main()
