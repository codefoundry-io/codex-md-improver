"""A metadata-only declaration does not make an absent global override nonempty."""
from pathlib import Path
import unittest

import test_file_policy_only as helpers


class MissingGlobalTests(unittest.TestCase):
    setUp = helpers.MetadataOnlyTests.setUp
    put = helpers.MetadataOnlyTests.put
    settings = helpers.MetadataOnlyTests.settings
    run_scan = helpers.MetadataOnlyTests.run_scan

    def test_absent_global_override_allows_definite_fallback(self):
        target = self.home / "AGENTS.override.md"
        fallback = self.put(self.home / "AGENTS.md", "global fallback")
        code, audit, _ = self.run_scan([target], cwd=True)
        self.assertIn(code, (0, 1))
        self.assertFalse(audit["partial"])
        source = audit["chains"][0]["global_source"]
        self.assertEqual(source["path"], str(fallback))
        self.assertEqual(source["state"], "selected")
        self.assertEqual(source["original_bytes"], len(b"global fallback"))
        self.assertEqual(audit["metadata_only_files"][0]["status"], "missing")
        self.assertFalse(source.get("conditional_sources"))


if __name__ == "__main__":
    unittest.main()
