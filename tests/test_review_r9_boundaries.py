"""Stored names and completed retargets preserve excluded boundaries."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
import md_improver


class StoredSkillNames(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes

    def test_directory_with_lowercase_skill_keeps_ordinary_siblings(self):
        lower = self.put(self.root / 'docs/skill.md', 'Ordinary lowercase text.')
        guide = self.put(self.root / 'docs/guide.md', 'Ordinary guide.')
        self.put(self.source, 'Read [docs](docs/).\n')
        graph = self.build()
        self.assertEqual({Path(r['terminal_path']).resolve() for r in self.routes(graph)}, {lower, guide})
        self.assertFalse(graph['partial'])

    def test_native_uppercase_alias_to_lowercase_file_is_read(self):
        lower = self.put(self.root / 'ordinary/skill.md', 'Ordinary lowercase text.')
        alias = lower.with_name('SKILL.md')
        if not alias.exists():
            self.skipTest('fixture volume is case-sensitive; native alias does not exist')
        self.assertTrue(alias.samefile(lower))
        self.put(self.source, 'Read [ordinary](ordinary/SKILL.md).\n')
        graph = self.build()
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(alias), 'leaf')])

    def test_directory_with_exact_skill_remains_excluded(self):
        self.put(self.root / 'docs/SKILL.md', 'Skill content.')
        self.put(self.root / 'docs/guide.md', 'Excluded sibling.')
        self.put(self.source, 'Read [docs](docs/).\n')
        graph = self.build()
        self.assertEqual([(r['terminal_path'], r['terminal_kind']) for r in self.routes(graph)],
                         [(str(self.root / 'docs'), 'excluded_skill')])


class CandidateRetarget(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def check_retarget(self, target_kind, shared=False):
        original = 'Sure! Read [nested](../old.md).\n'
        guide = self.put(self.root / 'docs/guide.md', original)
        good = self.put(self.root / 'docs/good.md', 'Sure! Keep the useful guide.\n')
        old = self.put(self.root / 'old.md', 'Sure! Original descendant.')
        storage = self.base / 'GitStore'
        self.put(self.root / '.git', 'gitdir: ../GitStore\n')
        self.put(storage / 'marker', 'metadata')
        targets = {'skill': self.base / 'deploy/SKILL.md', 'git': self.root / '.gitdir/.git/policy.md',
                   'external_git': storage / 'policy.md', 'ordinary': self.base / 'ordinary.md',
                   'prefix': self.base / 'GitStore-copy/policy.md', 'unchanged': None}
        target = targets[target_kind]
        if target is not None:
            self.put(target, original)
        self.put(self.source, 'Read [docs](docs/).\n' + ('Read [shared](old.md).\n' if shared else ''))
        settings = self.put(self.base / 'settings.json', json.dumps({
            'non_project': {'limit': 32768, 'root_markers': ['.git'], 'fallback_names': []},
            'trust': {str(self.root): 'trusted'}}))
        records = md_improver._candidate_records
        read_bytes = Path.read_bytes
        reads = []
        def replace_then_extract(graph, scenarios, content, selected):
            if target is not None:
                guide.unlink()
                guide.symlink_to(target)
            def track(path):
                if path == guide:
                    reads.append(str(path))
                return read_bytes(path)
            with patch.object(Path, 'read_bytes', track):
                return records(graph, scenarios, content, selected)
        out = self.base / 'scan'
        with patch.object(md_improver, '_candidate_records', replace_then_extract):
            code = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                                    '--codex-home', str(self.home), '--settings', str(settings), '--out', str(out)])
        audit = json.loads((out / 'audit.json').read_text())
        rows = [json.loads(line) for line in (out / 'routes.jsonl').read_text().splitlines()]
        if target_kind in {'skill', 'git', 'external_git'}:
            with self.subTest(check='no excluded physical read'):
                self.assertEqual(reads, [])
            with self.subTest(check='no excluded candidate'):
                self.assertFalse(any(c['path'] == str(guide) for c in audit['candidates']))
            with self.subTest(check='no stale route expansion'):
                self.assertEqual(any(Path(r['terminal_path']).resolve() == old for r in rows), shared)
            with self.subTest(check='descendant candidate reachability'):
                self.assertEqual(any(Path(c['path']).resolve() == old for c in audit['candidates']), shared)
            with self.subTest(check='explicit candidate boundary'):
                self.assertTrue(any(b['path'] == str(guide) and b.get('phase') == 'candidates'
                                    for b in audit['graph']['boundaries']))
        else:
            self.assertIn(code, (0, 1))
            self.assertFalse(audit['partial'])
            self.assertTrue(any(c['path'] == str(guide) for c in audit['candidates']))
            self.assertEqual({Path(r['terminal_path']).resolve() for r in rows}, {old, good})
        self.assertTrue(any(c['path'] == str(good) for c in audit['candidates']))

    def test_completed_retarget_to_skill(self): self.check_retarget('skill')
    def test_completed_retarget_to_git(self): self.check_retarget('git')
    def test_completed_retarget_to_external_git(self): self.check_retarget('external_git')
    def test_shared_descendant_survives_excluded_parent(self): self.check_retarget('skill', shared=True)
    def test_same_byte_ordinary_symlink_control(self): self.check_retarget('ordinary')
    def test_same_byte_sibling_prefix_control(self): self.check_retarget('prefix')
    def test_unchanged_regular_control(self): self.check_retarget('unchanged')
