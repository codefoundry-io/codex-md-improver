"""Package boundaries and installed resource resolution, without network access."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_skill", ROOT / "tools/package_skill.py")
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)
SKILL = ROOT / "skills/codex-md-improver"


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("CODEX_MD_TEST_TMP"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "codex-md-improver"
        shutil.copytree(SKILL, self.source)
        self.out = self.root / "out"

    def build(self):
        return PACKAGE.build_package(self.source, self.out, "0.1.0")

    def test_sorted_manifest_matches_archive_and_is_reproducible(self):
        result = self.build()
        self.assertTrue(result.get("archive"), "Build must return an archive")
        manifest = json.loads(Path(result["manifest"]).read_text())
        paths = [r["path"] for r in manifest["files"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertIn("LICENSE", paths)
        self.assertIn("references/assessment-format.md", paths)
        with zipfile.ZipFile(result["archive"]) as archive:
            self.assertEqual(set(archive.namelist()), {"codex-md-improver/" + p for p in paths} | {"codex-md-improver/MANIFEST.json"})
            for row in manifest["files"]:
                data = archive.read("codex-md-improver/" + row["path"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])
                self.assertEqual(len(data), row["size"])
        self.assertTrue(PACKAGE.verify_package(Path(result["archive"]), manifest))
        other = PACKAGE.build_package(self.source, self.root / "other", "0.1.0")
        self.assertEqual(Path(result["archive"]).read_bytes(), Path(other["archive"]).read_bytes())

    def test_unexpected_file_is_rejected_without_output(self):
        for rel in ("report.json", ".env", "scripts/__pycache__/bad.pyc", "fixtures/input.md", ".git/config"):
            with self.subTest(path=rel):
                p = self.source / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("unexpected")
                with self.assertRaises(ValueError):
                    self.build()
                self.assertFalse(self.out.exists())
                p.unlink()
                # Remove only empty fixture directories just introduced.
                while p.parent != self.source and p.parent.is_dir():
                    parent = p.parent
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    p = parent

    def test_missing_required_resource_is_rejected(self):
        (self.source / "assets/defaults.json").unlink()
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.out.exists())

    def test_escaping_file_or_directory_symlink_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "stolen.txt").write_text("do not package")
        path = self.source / "assets/defaults.json"
        path.unlink()
        path.symlink_to(outside / "stolen.txt")
        with self.assertRaises(ValueError):
            self.build()
        path.unlink()
        shutil.copyfile(SKILL / "assets/defaults.json", path)
        (self.source / "extra").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.build()

    def test_machine_specific_instruction_paths_are_rejected(self):
        path = self.source / "SKILL.md"
        original = path.read_text()
        for literal in ("/Users/private-user/code", "/home/private-user/source", "C:\\Users\\private-user\\code"):
            with self.subTest(literal=literal):
                path.write_text(original + "\nRead " + literal + "\n")
                with self.assertRaises(ValueError):
                    self.build()
                self.assertFalse(self.out.exists())

    def test_output_cannot_overlap_source_or_existing_directory(self):
        for out in (self.source / "dist", self.root, self.source.parent / "codex-md-improver"):
            with self.subTest(out=out), self.assertRaises(ValueError):
                PACKAGE.build_package(self.source, out, "0.1.0")
        self.assertFalse((self.source / "dist").exists())

    def test_invalid_version_is_rejected_before_output(self):
        for version in ("../../escape", "", "v1/2", "1.0.0;cmd"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                PACKAGE.build_package(self.source, self.out, version)
        self.assertFalse(self.out.exists())

    def test_hash_mismatch_and_duplicate_zip_entries_are_rejected(self):
        result = self.build()
        self.assertTrue(result.get("archive"), "Build must return an archive")
        manifest = json.loads(Path(result["manifest"]).read_text())
        changed = json.loads(json.dumps(manifest))
        changed["files"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            PACKAGE.verify_package(Path(result["archive"]), changed)
        bad = self.root / "bad.zip"
        with zipfile.ZipFile(result["archive"]) as src, zipfile.ZipFile(bad, "w") as dst:
            for name in src.namelist():
                data = src.read(name)
                dst.writestr(name, data + (b"tampered" if name.endswith("SKILL.md") else b""))
        with self.assertRaises(ValueError):
            PACKAGE.verify_package(bad, manifest)
        duplicate = self.root / "duplicate.zip"
        with zipfile.ZipFile(result["archive"]) as src, zipfile.ZipFile(duplicate, "w") as dst:
            for name in src.namelist():
                dst.writestr(name, src.read(name))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                dst.writestr("codex-md-improver/SKILL.md", src.read("codex-md-improver/SKILL.md"))
        with self.assertRaises(ValueError):
            PACKAGE.verify_package(duplicate, manifest)

    def test_repository_discovery_and_notice_equality(self):
        link = ROOT / ".agents/skills/codex-md-improver"
        self.assertTrue(link.is_symlink(), "Repository discovery must use the selected symlink")
        self.assertEqual(link.resolve(), SKILL.resolve())
        self.assertTrue((ROOT / "LICENSE").is_file())
        self.assertTrue((SKILL / "LICENSE").is_file())
        self.assertEqual((ROOT / "LICENSE").read_bytes(), (SKILL / "LICENSE").read_bytes())

    def test_installed_subtree_runs_from_unrelated_cwd(self):
        installed = self.root / "discovery/.agents/skills/codex-md-improver"
        shutil.copytree(self.source, installed)
        target = self.root / "target"
        target.mkdir()
        (target / ".git").mkdir()
        (target / ".git/HEAD").write_text("ref: refs/heads/main\n")
        (target / "AGENTS.md").write_text("Keep useful examples.\n")
        home = self.root / "home"
        home.mkdir()
        settings = self.root / "settings.json"
        settings.write_text(json.dumps({"trust": {str(target): "trusted"}}))
        proc = subprocess.run([sys.executable, "-B", str(installed / "scripts/md_improver.py"), "scan",
                               "--project", str(target), "--codex-home", str(home), "--settings", str(settings),
                               "--out", str(self.root / "scan")], cwd=target, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((installed / "LICENSE").is_file())
        self.assertEqual((self.source / "LICENSE").read_bytes(), (installed / "LICENSE").read_bytes())
        self.assertFalse(list(installed.rglob("*.pyc")))


if __name__ == "__main__":
    unittest.main()
