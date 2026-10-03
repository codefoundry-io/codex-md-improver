"""Native-volume regressions for package output containment."""
import importlib.util
from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "r12_distribution_fixture", PROJECT / "tests/test_distribution.py"
)
distribution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(distribution)
PACKAGE = distribution.PACKAGE


class PackageNativeCaseContainmentTests(unittest.TestCase):
    def setUp(self):
        # Reuse the official disposable source copy and CODEX_MD_TEST_TMP root.
        # Do not subclass its TestCase: its existing tests must not be collected
        # again from this private regression file.
        distribution.DistributionTests.setUp(self)

    def source_bytes(self):
        return {
            path.relative_to(self.source).as_posix(): path.read_bytes()
            for path in self.source.rglob("*") if path.is_file()
        }

    def native_case_alias(self):
        alias = self.source.with_name(self.source.name.upper())
        if not alias.exists() or not alias.samefile(self.source):
            self.skipTest("Fixture volume does not expose a native case-insensitive alias")
        return alias

    def assert_rejected_before_creation(self, output, missing_parent=None):
        before = self.source_bytes()
        self.assertFalse(output.exists())
        if missing_parent is not None:
            self.assertFalse(missing_parent.exists())
        rejected = False
        try:
            PACKAGE.build_package(self.source, output, "0.1.0")
        except ValueError:
            rejected = True
        finally:
            # Even a failing implementation must preserve the copied canonical
            # resource bytes. Output absence below also forbids added artifacts.
            for name, data in before.items():
                self.assertEqual((self.source / name).read_bytes(), data, name)
        self.assertFalse(output.exists(), "Containment rejection must precede output creation")
        if missing_parent is not None:
            self.assertFalse(missing_parent.exists(), "Rejection must not create output parents")
        self.assertEqual(self.source_bytes(), before)
        self.assertTrue(rejected, "Source-contained output must raise ValueError")

    def assert_valid_outside_output(self, output):
        before = self.source_bytes()
        self.assertFalse(output.exists())
        result = PACKAGE.build_package(self.source, output, "0.1.0")
        self.assertTrue(output.is_dir())
        self.assertEqual(Path(result["archive"]).parent, output)
        self.assertEqual(Path(result["manifest"]).parent, output)
        self.assertTrue(Path(result["archive"]).is_file())
        self.assertTrue(Path(result["manifest"]).is_file())
        self.assertEqual(self.source_bytes(), before)

    def test_native_case_alias_child_is_rejected_before_creation(self):
        alias = self.native_case_alias()
        self.assert_rejected_before_creation(alias / "dist")

    def test_native_case_alias_missing_parent_is_rejected_before_creation(self):
        alias = self.native_case_alias()
        missing_parent = alias / "missing-parent" / "nested"
        self.assert_rejected_before_creation(missing_parent / "dist", alias / "missing-parent")

    def test_outside_output_with_missing_parents_is_allowed(self):
        output = self.root / "outside" / "missing-parent" / "dist"
        self.assertFalse(output.parent.exists())
        self.assert_valid_outside_output(output)
        self.assertTrue(output.parent.is_dir())

    def test_similarly_prefixed_source_sibling_is_allowed(self):
        output = self.source.with_name(self.source.name + "-distribution")
        self.assert_valid_outside_output(output)

    def test_missing_path_helper_preserves_non_directory_failure(self):
        ordinary = self.root / "ordinary-file"
        ordinary.write_text("data")
        with self.assertRaises(NotADirectoryError):
            PACKAGE._path_identity.canonical_missing(ordinary / ".." / "future")
        self.assertFalse((self.root / "future").exists())


if __name__ == "__main__":
    unittest.main()
