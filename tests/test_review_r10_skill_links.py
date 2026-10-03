"""Stored SKILL entrypoints retain their boundary through symlinks."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
from discovery import _Content
from reporting import enrich_audit, report_hash
import md_improver


class StoredSkillLinks(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def tree(self):
        target = self.put(self.root / 'docs/guide.md', 'Sure! Read [child](child.md).\n')
        self.put(self.root / 'docs/child.md', 'Nested instructions.')
        self.put(self.root / 'deploy/child.md', 'Nested instructions.')
        link = self.root / 'deploy/SKILL.md'
        link.symlink_to(target)
        return target, link

    def test_stored_symlink_is_excluded_for_file_and_directory_routes(self):
        target, link = self.tree()
        for reference, terminal in (('deploy/SKILL.md', link), ('deploy/', link.parent)):
            with self.subTest(reference=reference):
                self.put(self.source, f'Read [deployment]({reference}).\n')
                reads = []
                original = Path.read_bytes
                def track(path):
                    if path.samefile(target): reads.append(str(path))
                    return original(path)
                with patch.object(Path, 'read_bytes', track): graph = self.build()
                with self.subTest(check='no skill byte read'): self.assertEqual(reads, [])
                with self.subTest(check='consistent boundary'):
                    self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                                     [(str(terminal), 'excluded_skill')])

    def test_explicit_support_file_and_ordinary_target_remain_readable(self):
        target, link = self.tree()
        for reference, leaf in (('deploy/child.md', link.parent / 'child.md'),
                                ('docs/guide.md', target.parent / 'child.md')):
            with self.subTest(reference=reference):
                self.put(self.source, f'Read [ordinary]({reference}).\n')
                graph = self.build()
                self.assertEqual({r['terminal_path'] for r in self.routes(graph)}, {str(leaf)})
                self.assertFalse(graph['partial'])

    def test_skill_entry_parent_metadata_failure_is_branch_local(self):
        _, link = self.tree()
        self.put(self.source, 'Read [deployment](deploy/SKILL.md).\n')
        original = Path.iterdir
        def denied(path):
            if path == link.parent: raise PermissionError('Stored-name metadata denied')
            return original(path)
        with patch.object(Path, 'iterdir', denied): graph = self.build()
        self.assertTrue(graph['partial'])
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(link), 'blocked_frontier')])


class StoredNameRetarget(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def prepare(self):
        text = 'Require approval.\nKeep scope narrow.\n'
        self.guide = self.put(self.root / 'deploy/skill.md', text)
        self.upper = self.guide.with_name('SKILL.md')
        if not self.upper.exists():
            self.skipTest('fixture volume is case-sensitive; native alias does not exist')
        self.assertTrue(self.upper.samefile(self.guide))
        self.payload = self.put(self.base / 'ordinary.md', text)
        self.put(self.source, 'Read [guide](deploy/skill.md).\n')

    def replace(self):
        self.guide.unlink()
        self.upper.symlink_to(self.payload)
        self.assertTrue(self.guide.samefile(self.upper))

    def scan(self, out):
        return md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                                '--codex-home', str(self.home), '--out', str(out)])

    def test_native_candidate_stored_symlink_retarget_is_excluded_before_read(self):
        self.prepare()
        records, read = md_improver._candidate_records, _Content.read
        reads = []
        def retarget(graph, scenarios, content, selected):
            self.replace()
            def track(cache, path):
                if path == self.guide: reads.append(str(path))
                return read(cache, path)
            with patch.object(_Content, 'read', track): return records(graph, scenarios, content, selected)
        out = self.base / 'scan'
        with patch.object(md_improver, '_candidate_records', retarget): code = self.scan(out)
        with self.subTest(check='excluded before content read'): self.assertEqual(reads, [])
        with self.subTest(check='partial retarget observation'): self.assertEqual(code, 3)
        audit = json.loads((out / 'audit.json').read_text())
        self.assertTrue(any(b['path'] == str(self.guide) and b['kind'] == 'excluded_skill'
                            for b in audit['graph']['boundaries']))

    def test_native_report_stored_symlink_retarget_is_excluded_before_read(self):
        self.prepare()
        out = self.base / 'scan'
        self.assertEqual(self.scan(out), 0)
        audit = json.loads((out / 'audit.json').read_text())
        reviewed = [{'source': alias, 'source_sha256': node['sha256']}
                    for node in audit['graph']['nodes'].values() for alias in node['aliases']]
        reviewed.sort(key=lambda row: row['source'] != str(self.guide))
        assessment = {'schema_version': 1, 'audit_sha256': report_hash(audit),
                      'reviewed_sources': reviewed, 'semantic_review_complete': True}
        self.replace()
        reads = []
        read = _Content.read
        def track(cache, path):
            reads.append(str(path))
            return read(cache, path)
        with patch.object(_Content, 'read', track):
            with self.assertRaisesRegex(ValueError, 'excluded source'):
                enrich_audit(audit, assessment)
        self.assertEqual(reads, [])
