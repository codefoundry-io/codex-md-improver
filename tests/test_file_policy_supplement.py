"""Plan R3 minor findings: persisted identity and independent loader gates."""
import copy
import hashlib
import unittest
from unittest.mock import patch
from pathlib import Path

import test_file_policy_only as helpers
from discovery import ScopeRequest, scan
from reporting import enrich_audit, report_hash


class SupplementTests(unittest.TestCase):
    setUp = helpers.MetadataOnlyTests.setUp
    put = helpers.MetadataOnlyTests.put
    settings = helpers.MetadataOnlyTests.settings
    run_scan = helpers.MetadataOnlyTests.run_scan
    guard = helpers.MetadataOnlyTests.guard

    def test_enrichment_retains_scan_identity_after_declared_path_moves(self):
        target = self.put(self.root / "hold.md", "secret")
        self.put(self.source, "[hold](hold.md)")
        settings = self.settings([])
        settings.pop("metadata_only_paths")
        with patch.object(self, "settings", return_value=settings):
            _, audit, _ = self.run_scan([], cwd=True)
        info = target.stat()
        moved = self.root / "moved.md"
        target.rename(moved)
        audit["scope"]["settings"]["metadata_only_paths"] = [str(target)]
        audit["metadata_only_files"] = [{"path": str(target), "status": "regular_file",
            "reason": "metadata_only", "metadata_bytes": 6,
            "physical_identity": [info.st_dev, info.st_ino]}]
        node = next(n for n in audit["graph"]["nodes"].values() if str(target) in n["aliases"])
        node["aliases"].append(str(moved))
        assessment = {"schema_version": 1, "audit_sha256": report_hash(audit),
            "reviewed_sources": [{"source": str(moved),
                                 "source_sha256": hashlib.sha256(b"secret").hexdigest()}]}
        with self.guard(moved), self.assertRaises(ValueError):
            enrich_audit(audit, assessment)

    def test_denied_guidance_keeps_known_zero_and_untrusted_gates(self):
        for gate in ("zero", "untrusted"):
            with self.subTest(gate=gate):
                settings = self.settings([self.source])
                if gate == "zero":
                    settings["session_overrides"] = {"limit": 0}
                else:
                    settings["trust"][str(self.root)] = "untrusted"
                with self.guard(self.source):
                    audit = scan(ScopeRequest([self.root], self.home, self.root, settings))
                chain = audit["chains"][0]
                self.assertEqual(chain["loader_outcome"], "omitted_by_gate")
                self.assertEqual(chain["project_included_bytes"], 0)
                self.assertIsNone(chain["modeled_loader_error"])
                self.assertTrue(audit["partial"])


if __name__ == "__main__":
    unittest.main()
