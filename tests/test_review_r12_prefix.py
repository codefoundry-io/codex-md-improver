"""Pinned trust paths normalize redundant POSIX roots before key lookup."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
import test_review_r12_trust as trust_fixtures
from discovery import resolve_settings


class TrustRootNormalization(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    linked = trust_fixtures.PinnedTrustPaths.linked
    request = trust_fixtures.PinnedTrustPaths.request

    def resolve(self, double_key):
        main, _, admin = self.linked()
        self.put(self.root / '.git', 'gitdir: /' + str(admin) + '\n')
        self.put(self.root / '.codex/config.toml',
                 'project_doc_max_bytes = 7\nproject_doc_fallback_filenames = ["LOCAL.md"]\n')
        key = '/' + str(main) if double_key else str(main)
        return main, resolve_settings(self.request(main, {key: 'trusted'}), self.root)

    def test_double_slash_original_key_does_not_grant_trust(self):
        _, settings = self.resolve(True)
        self.assertEqual(settings.trust, 'unset')
        self.assertIsNone(settings.trust_key)
        self.assertEqual(settings.limit, 1000)
        self.assertEqual(settings.fallback_names, ['BASE.md'])

    def test_single_root_key_with_double_slash_pointer_control(self):
        main, settings = self.resolve(False)
        self.assertEqual((settings.trust, settings.trust_key), ('trusted', str(main)))
        self.assertEqual(settings.limit, 7)
        self.assertEqual(settings.fallback_names, ['LOCAL.md'])
