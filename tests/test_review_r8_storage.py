"""Post-scan evidence revalidation preserves known external Git boundaries."""
import hashlib
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


class RecordedGitBoundary(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def scanned_input(self):
        text = 'Require approval.\nKeep scope narrow.\n'
        self.storage = self.base / 'GitStore'
        self.payload = self.put(self.storage / 'policy.md', text)
        self.put(self.root / '.git', 'gitdir: ../GitStore\n')
        self.put(self.source, 'Read [guide](guide.md).\n')
        self.guide = self.put(self.root / 'guide.md', text)
        settings = self.put(self.base / 'settings.json', json.dumps({
            'non_project': {'limit': 32768, 'root_markers': ['.git'], 'fallback_names': []},
            'trust': {str(self.root): 'trusted'}}))
        out = self.base / 'scan'
        code = md_improver.main(['scan', '--project', str(self.root), '--cwd', str(self.root),
                                '--codex-home', str(self.home), '--settings', str(settings), '--out', str(out)])
        self.assertEqual(code, 0)
        audit = json.loads((out / 'audit.json').read_text())
        self.assertTrue(any(row == {'path': str(self.storage), 'kind': 'git_administration'}
                            for row in audit['frontiers']))
        digest = hashlib.sha256(self.guide.read_bytes()).hexdigest()
        self.assertTrue(any(str(self.guide) in n['aliases'] and n['sha256'] == digest
                            for n in audit['graph']['nodes'].values()))
        assessment = {'schema_version': 1, 'audit_sha256': report_hash(audit),
                      'reviewed_sources': [{'source': str(self.guide), 'source_sha256': digest}],
                      'semantic_review_complete': True}
        assessment['reviewed_sources'] += [
            {'source': alias, 'source_sha256': node['sha256']}
            for node in audit['graph']['nodes'].values() for alias in node['aliases']
            if alias != str(self.guide) and node.get('content_status') == 'read']
        return audit, assessment, text

    def test_same_byte_symlink_into_recorded_git_storage_is_rejected(self):
        audit, assessment, _ = self.scanned_input()
        self.guide.unlink()
        self.guide.symlink_to(self.payload)
        self.assertEqual(hashlib.sha256(self.guide.read_bytes()).hexdigest(),
                         assessment['reviewed_sources'][0]['source_sha256'])
        reads = []
        original = _Content.read
        def track(content, path):
            reads.append(str(path))
            return original(content, path)
        with patch.object(_Content, 'read', track):
            with self.assertRaisesRegex(ValueError, 'excluded source'):
                enrich_audit(audit, assessment)
        self.assertEqual(reads, [])

    def test_unchanged_regular_source_control(self):
        audit, assessment, _ = self.scanned_input()
        result = enrich_audit(audit, assessment)
        self.assertEqual(result['exit_code'], 0)

    def test_same_byte_symlink_to_sibling_prefix_is_not_excluded(self):
        audit, assessment, text = self.scanned_input()
        ordinary = self.put(self.base / 'GitStore-copy/policy.md', text)
        self.guide.unlink()
        self.guide.symlink_to(ordinary)
        result = enrich_audit(audit, assessment)
        self.assertEqual(result['exit_code'], 0)
