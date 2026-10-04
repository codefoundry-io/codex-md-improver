"""Preserve global file selection and legacy streamed secondary controls."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import unittest

import test_file_policy_only as helpers
from md_improver import main


@contextmanager
def pipe_json(value):
    reader, writer = os.pipe()
    try:
        os.write(writer, json.dumps(value).encode())
    finally:
        os.close(writer)
    try:
        yield "/dev/fd/" + str(reader)
    finally:
        os.close(reader)


class MetadataCompatibilityTests(unittest.TestCase):
    setUp = helpers.MetadataOnlyTests.setUp
    put = helpers.MetadataOnlyTests.put
    settings = helpers.MetadataOnlyTests.settings
    run_scan = helpers.MetadataOnlyTests.run_scan
    guard = helpers.MetadataOnlyTests.guard

    def test_directory_is_not_a_conditional_global_file(self):
        target = self.put(self.home / "AGENTS.override.md", "protected")
        leaf = self.put(self.home / "AGENTS.md/leaf.md", "not global guidance")
        with self.guard(target):
            code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        self.assertFalse(audit["chains"][0]["global_source"]["conditional_sources"])
        self.assertNotIn(str(leaf), {a for n in audit["graph"]["nodes"].values() for a in n["aliases"]})

    def test_resolutions_pipe_remains_supported_without_metadata_policy(self):
        settings = self.settings([])
        settings.pop("metadata_only_paths")
        settings_path = self.put(self.base / "settings.json", json.dumps(settings))
        with pipe_json([]) as pipe:
            code = main(["scan", "--project", str(self.root), "--codex-home", str(self.home),
                         "--cwd", str(self.root), "--settings", str(settings_path),
                         "--resolutions", pipe, "--out", str(self.base / "pipe-scan")])
        self.assertIn(code, (0, 1))

    def test_assessment_pipe_remains_supported_with_empty_metadata_policy(self):
        _, audit, out = self.run_scan([], cwd=True)
        self.assertIsNotNone(audit)
        assessment = {"schema_version": 1,
                      "audit_sha256": hashlib.sha256((out / "audit.json").read_bytes()).hexdigest()}
        with pipe_json(assessment) as pipe:
            code = main(["report", "--audit", str(out / "audit.json"), "--assessment", pipe,
                         "--out", str(self.base / "pipe-report")])
        # Accepted input remains semantically unassessed, a legitimate partial report.
        self.assertEqual(code, 3)
        manifest = json.loads((self.base / "pipe-report/manifest.json").read_text())
        self.assertEqual(manifest["phase"], "finished")
        self.assertTrue((self.base / "pipe-report/audit.json").is_file())


if __name__ == "__main__":
    unittest.main()
