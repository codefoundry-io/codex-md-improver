"""Hand-derived loader and CLI conformance; targets remain read-only."""
import ast
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOT = Path(__file__).resolve().parents[1] / "skills/codex-md-improver"
sys.path.insert(0, str(SOT / "scripts"))
from discovery import ScopeRequest, discover_chains, resolve_settings, scan


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="codex-md-task1-", dir=os.environ.get("CODEX_MD_TEST_TMP"))
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "project"
        self.home = self.base / "codex-home"
        self.root.mkdir()
        self.home.mkdir()
        self.put(self.root / ".git/HEAD", "ref: refs/heads/main\n")
        self.put(self.root / "AGENTS.md", "root instructions")

    def put(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode())
        return path

    def trust(self, entries=None, extra=""):
        entries = entries or {self.root: "trusted"}
        text = extra + "\n"
        for key, value in entries.items():
            text += "[projects." + json.dumps(str(key)) + "]\n"
            if value != "unset":
                text += 'trust_level = "' + value + '"\n'
        self.put(self.home / "config.toml", text)

    def request(self, settings=None, cwd=None, projects=None):
        return ScopeRequest(projects or [self.root], self.home, cwd, settings or {})

    def chain(self, cwd=None, settings=None):
        rows = discover_chains(self.request(settings, cwd or self.root))
        self.assertTrue(rows, "baseline has no discovered instruction chain")
        return rows[0]

    def cli(self, settings=None, extra=()):
        argv = [sys.executable, str(SOT / "scripts/md_improver.py"), "scan",
                "--project", str(self.root), "--codex-home", str(self.home)]
        if settings is not None:
            path = self.put(self.base / "settings.json", json.dumps(settings))
            argv += ["--settings", str(path)]
        out = self.base / ("run-" + str(len(list(self.base.glob("run-*")))))
        proc = subprocess.run(argv + list(extra) + ["--out", str(out)], capture_output=True, text=True)
        report = json.loads((out / "audit.json").read_text()) if (out / "audit.json").exists() else None
        return proc, report

    def test_override_and_fallback_selection(self):
        self.put(self.root / "AGENTS.override.md", "override")
        row = self.chain()
        self.assertEqual([Path(x["path"]).name for x in row["sources"]], ["AGENTS.override.md"])
        self.assertEqual(row["project_included_bytes"], 8)
        (self.root / "AGENTS.override.md").unlink()
        (self.root / "AGENTS.md").unlink()
        self.put(self.root / "GUIDE.md", "fallback")
        row = self.chain(settings={"non_project": {"fallback_names": ["", ".", "..", "x/y", "GUIDE.md", "GUIDE.md"]}})
        self.assertEqual([Path(x["path"]).name for x in row["sources"]], ["GUIDE.md"])
        self.assertEqual(row["settings"]["fallback_names"], ["GUIDE.md"])

    def test_empty_override_shadows_ordinary(self):
        self.put(self.root / "AGENTS.override.md", "")
        self.assertEqual(self.chain()["project_included_bytes"], 0)

    def test_sibling_regions_not_combined(self):
        self.put(self.root / "a/AGENTS.md", "A")
        self.put(self.root / "b/AGENTS.md", "BB")
        rows = discover_chains(self.request())
        self.assertEqual(len(rows), 3)
        self.assertEqual({Path(r["cwd"]).name: r["project_original_bytes"] for r in rows},
                         {"project": 17, "a": 18, "b": 19})

    def test_identical_chain_different_config_region(self):
        self.trust()
        self.put(self.root / "AGENTS.md", "x" * 20000)
        self.put(self.root / "a/.codex/config.toml", "project_doc_max_bytes = 16384\nproject_root_markers = []\n")
        (self.root / "b").mkdir()
        a, b = self.chain(self.root / "a"), self.chain(self.root / "b")
        self.assertEqual((a["project_included_bytes"], b["project_included_bytes"]), (16384, 20000))
        self.assertEqual(a["scenario_project_root"], str(self.root))
        self.assertNotEqual(a["region_id"], b["region_id"])

    def test_default_cli_observed_trusted_root_subdirectories(self):
        self.trust()
        self.put(self.root / "AGENTS.md", "x" * 32769)
        (self.root / "a").mkdir()
        (self.root / "b").mkdir()
        proc, report = self.cli()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(len(report["chains"]), 3)
        for row in report["chains"]:
            self.assertEqual(row["project_included_bytes"], 32768)
            self.assertEqual(row["settings"]["trust_key"], str(self.root))
            self.assertEqual(row["settings"]["provenance"]["scenario"], "observed_plus_defaults")
            self.assertTrue(row["settings"]["provenance"]["unattested_live_layers"])

    def test_supplied_root_trust_and_cwd_priority(self):
        child = self.root / "child"
        child.mkdir()
        for level in ("trusted", "untrusted", "unset", "unknown"):
            with self.subTest(level=level):
                settings = {"trust": {str(self.root): "trusted", str(child): level}}
                actual = resolve_settings(self.request(settings), child)
                self.assertEqual(actual.trust, level)
                self.assertEqual(actual.trust_key, str(child))
        actual = resolve_settings(self.request({"trust": {str(self.root): "trusted"}}), child)
        self.assertEqual(actual.trust, "trusted")

    def test_unset_observed_cwd_blocks_root_and_nested_repo_does_not_inherit(self):
        child = self.root / "child"
        child.mkdir()
        self.trust({self.root: "trusted", child: "unset"})
        self.assertEqual(resolve_settings(self.request(), child).trust, "unset")
        self.put(child / ".git/HEAD", "ref: refs/heads/main\n")
        self.trust()
        self.assertEqual(resolve_settings(self.request(), child).trust, "unset")

    def test_submodule_negative_validation_is_not_unknown_or_parent_trust(self):
        self.trust()
        child = self.root / "submodule"
        self.put(child / ".git", "gitdir: ../.git/modules/submodule\n")
        self.put(self.root / ".git/modules/submodule/HEAD", "ref: refs/heads/main\n")
        self.put(child / "AGENTS.md", "module")
        self.assertEqual(resolve_settings(self.request(), child).trust, "unset")
        self.assertEqual(self.chain(child)["project_included_bytes"], 6)

    def test_validated_linked_worktree_and_mismatch(self):
        self.trust()
        linked = self.base / "linked"
        admin = self.root / ".git/worktrees/linked"
        self.put(linked / ".git", "gitdir: " + str(admin) + "\n")
        self.put(admin / "gitdir", str(linked / ".git") + "\n")
        self.put(admin / "commondir", "../..\n")
        request = self.request(projects=[linked])
        self.assertEqual(resolve_settings(request, linked).trust, "trusted")
        self.put(admin / "gitdir", str(self.root / ".git") + "\n")
        self.assertEqual(resolve_settings(request, linked).trust, "unset")

    def test_unknown_effective_settings_are_labeled(self):
        self.put(self.home / "config.toml", "invalid = [")
        settings = resolve_settings(self.request(), self.root)
        self.assertTrue(settings.unresolved)
        self.assertIsNone(self.chain()["project_included_bytes"])
        proc, report = self.cli()
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertTrue(report["partial"])

    def test_denied_config_is_partial_not_default(self):
        self.trust()
        original = Path.read_bytes
        config = self.home / "config.toml"
        def read(path):
            if path == config:
                raise PermissionError("synthetic denial")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            self.assertTrue(resolve_settings(self.request(), self.root).unresolved)
            self.assertEqual(scan(self.request())["exit_code"], 3)

    def test_settings_precedence_and_non_project_markers(self):
        self.trust(extra="project_doc_max_bytes = 100\n")
        self.put(self.root / ".codex/config.toml", "project_doc_max_bytes = 80\nproject_root_markers = []\n")
        settings = {"non_project": {"limit": 90}, "session_overrides": {"limit": 70}}
        resolved = resolve_settings(self.request(settings), self.root)
        self.assertEqual(resolved.limit, 70)
        self.assertEqual(resolved.root_markers, [".git"])
        self.assertEqual(resolve_settings(self.request({"non_project": {"limit": 90}}), self.root).limit, 80)

    def test_cwd_narrowing_and_ancestor_root(self):
        self.put(self.root / "a/AGENTS.md", "child")
        row = self.chain(self.root / "a")
        self.assertEqual(row["project_original_bytes"], 22)
        report = scan(self.request(cwd=self.root / "a", projects=[self.root / "a"]))
        self.assertEqual(len(report["chains"]), 1)
        self.assertEqual(report["chains"][0]["scenario_project_root"], str(self.root))
        self.assertEqual(self.chain(self.root / "a", {"non_project": {"root_markers": []}})["project_original_bytes"], 5)

    def test_inventory_keeps_vendor_and_alias_members(self):
        self.put(self.root / "vendor/readme.txt", "not guidance")
        (self.root / "alias").symlink_to(self.root / "vendor", target_is_directory=True)
        (self.root / "vendor/cycle").symlink_to(self.root, target_is_directory=True)
        report = scan(self.request())
        self.assertEqual({Path(r["cwd"]).name for r in report["chains"]}, {"project", "vendor", "alias"})
        self.assertFalse(report["partial"])
        self.assertTrue(any(f["kind"] == "cycle" for f in report["frontiers"]))

    def test_outside_inventory_alias_and_explicit_second_project(self):
        outside = self.base / "outside"
        self.put(outside / "AGENTS.md", "external")
        (self.root / "outside").symlink_to(outside, target_is_directory=True)
        proc, _ = self.cli()
        self.assertEqual(proc.returncode, 3)
        proc, report = self.cli(extra=["--project", str(outside)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(report["chains"]), 3)

    def test_warning_and_clipping_boundaries(self):
        for size, warning, excess, included in [(29491, False, False, 29491), (29492, True, False, 29492),
                                                 (32768, True, False, 32768), (32769, True, True, 32768)]:
            with self.subTest(size=size):
                self.put(self.root / "AGENTS.md", "x" * size)
                row = self.chain()
                self.assertEqual((row["warning"], row["raw_volume_exceeds_budget"], row["project_included_bytes"]),
                                 (warning, excess, included))

    def test_whitespace_and_lossy_accounting(self):
        self.put(self.root / "AGENTS.md", " " * 40000)
        self.put(self.root / "a/AGENTS.md", "x" * 100)
        row = self.chain(self.root / "a")
        self.assertEqual((row["project_original_bytes"], row["project_included_bytes"], row["project_retained_raw_bytes"]), (40100, 100, 100))
        self.put(self.root / "AGENTS.md", "한")
        row = self.chain(settings={"non_project": {"limit": 1}})
        self.assertEqual((row["project_retained_raw_bytes"], row["project_included_bytes"]), (1, 3))
        for text, expected in [("\u001c\u001d\u001e\u001f", 4), ("\u2003\u0085\n", 0)]:
            self.put(self.root / "AGENTS.md", text)
            self.assertEqual(self.chain()["project_included_bytes"], expected)

    def test_untrusted_unknown_and_zero_gates(self):
        for level, limit, expected in [("untrusted", None, 0), ("unknown", 0, 0), ("unknown", 50, None)]:
            settings = {"trust": {str(self.root): level}, "session_overrides": {"limit": limit}}
            self.assertEqual(self.chain(settings=settings)["project_included_bytes"], expected)

    def test_global_selection_lossy_trim_and_no_project_charge(self):
        self.put(self.home / "AGENTS.override.md", "\u2003\n")
        self.put(self.home / "AGENTS.md", b"  hello\xff  ")
        row = self.chain()
        self.assertEqual(row["global_source"]["original_bytes"], 10)
        self.assertEqual(row["global_source"]["included_bytes"], 8)
        self.assertEqual(row["project_included_bytes"], 17)
        self.put(self.home / "AGENTS.override.md", "x" * 40000)
        row = self.chain()
        self.assertEqual(row["global_source"]["included_bytes"], 40000)
        self.assertFalse(row["warning"])

    def test_global_failure_falls_through_and_cache_unknown(self):
        upper = self.put(self.home / "AGENTS.override.md", "upper")
        lower = self.put(self.home / "AGENTS.md", "lower")
        original = Path.read_bytes
        def read(path):
            if path == upper:
                raise PermissionError("synthetic")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            self.assertEqual(self.chain()["global_source"]["included_bytes"], 5)
            lower.unlink()
            self.assertEqual(self.chain()["global_source"]["state"], "cache_unknown")
        upper.unlink()
        self.assertEqual(self.chain()["global_source"]["state"], "absent")

    def test_simultaneous_group_budget_and_effective_record(self):
        self.put(self.root / "AGENTS.md", "한")
        other = self.base / "other"
        self.put(other / "AGENTS.md", "abc")
        group = {"id": "pair", "cwds": [str(self.root), str(other)],
                 "effective_loader_settings": {"limit": 4, "fallback_names": [], "root_markers": [], "trust": "trusted"}}
        report = scan(self.request({"environment_groups": [group]}, projects=[self.root, other]))
        self.assertEqual(len(report["groups"]), 1)
        self.assertEqual([r["project_included_bytes"] for r in report["groups"][0]["members"]], [3, 1])
        self.assertEqual(len(report["chains"]), 2)
        for effective, expected in [({}, None), ({"trust": "untrusted"}, 0), ({"limit": 0}, 0)]:
            group["effective_loader_settings"] = effective
            report = scan(self.request({"environment_groups": [group]}, projects=[self.root, other]))
            self.assertEqual(report["groups"][0]["project_included_bytes"], expected)

    def test_later_group_failure_conditions_earlier_and_global_delivery(self):
        other = self.base / "other"
        bad = self.put(other / "AGENTS.md", "bad")
        self.put(self.home / "AGENTS.md", "global")
        group = {"id": "pair", "cwds": [str(self.root), str(other)],
                 "effective_loader_settings": {"limit": 100, "fallback_names": [], "root_markers": [], "trust": "trusted"}}
        original = Path.read_bytes
        def read(path):
            if path == bad:
                raise PermissionError("synthetic")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            report = scan(self.request({"environment_groups": [group]}, projects=[self.root, other]))
        self.assertTrue(report["groups"], "baseline has no modeled groups")
        modeled = report["groups"][0]
        self.assertEqual(modeled["members"][0]["project_included_bytes"], 17)
        self.assertEqual(modeled["global_candidate_bytes"], 6)
        self.assertIsNone(modeled["delivered_bytes"])
        self.assertEqual(modeled["delivery"], "conditional_on_runtime_permissions")
        self.assertIn("propagated_failure", modeled["possible_outcomes"])

    def test_read_failure_and_metadata_exhaustion_order(self):
        child = self.root / "child"
        bad = self.put(child / "AGENTS.md", "child")
        original_read, original_stat = Path.read_bytes, Path.stat
        def read(path):
            if path == bad:
                raise PermissionError("read")
            return original_read(path)
        with patch.object(Path, "read_bytes", read):
            self.assertEqual(self.chain(child, {"non_project": {"limit": 17}})["project_included_bytes"], 17)
            self.assertIsNone(self.chain(child)["project_included_bytes"])
        def metadata(path, *args, **kwargs):
            if path == bad:
                raise PermissionError("metadata")
            return original_stat(path, *args, **kwargs)
        with patch.object(Path, "stat", metadata):
            self.assertIsNone(self.chain(child, {"non_project": {"limit": 17}})["project_included_bytes"])
            self.assertEqual(self.chain(child, {"non_project": {"limit": 0}})["project_included_bytes"], 0)

    def test_cli_strict_schema_and_output_boundary(self):
        for settings in [{"unexpected": True}, {"non_project": {"limit": True}}, {"trust": {"relative": "trusted"}}]:
            proc, _ = self.cli(settings)
            self.assertEqual(proc.returncode, 2, proc.stderr)
        proc = subprocess.run([sys.executable, str(SOT / "scripts/md_improver.py"), "scan", "--project", str(self.root),
                               "--codex-home", str(self.home), "--out", str(self.root / "result")], capture_output=True)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse((self.root / "result").exists())

    def test_home_selection_environment_blank_and_missing(self):
        self.put(self.home / "AGENTS.md", "home guide")
        with patch.dict(os.environ, {"CODEX_HOME": str(self.home)}):
            rows = discover_chains(ScopeRequest([self.root], cwd=self.root))
        self.assertTrue(rows, "baseline has no discovered chain")
        self.assertEqual(rows[0]["global_source"]["included_bytes"], 10)
        with patch.dict(os.environ, {"CODEX_HOME": ""}), patch.object(Path, "home", return_value=self.base):
            rows = discover_chains(ScopeRequest([self.root], cwd=self.root))
        self.assertEqual(rows[0]["global_source"]["state"], "absent")
        self.assertEqual(rows[0]["global_source"]["home_origin"], "default")
        with patch.dict(os.environ, {"CODEX_HOME": str(self.base / "missing")}):
            with self.assertRaises(ValueError):
                discover_chains(ScopeRequest([self.root], cwd=self.root))

    def test_native_case_canonical_trust_precedence(self):
        stored = self.root / "MiXeDCaseDir"
        stored.mkdir()
        alias = self.root / "mixedcasedir"
        insensitive = alias.exists()
        print("native-volume-case-insensitive=" + str(insensitive))
        if not insensitive:
            self.assertFalse(alias.exists())
            return
        self.assertTrue(os.path.samefile(stored, alias))
        if sys.platform != "darwin":
            self.skipTest("native canonical spelling fixture currently defined for macOS")
        import ctypes
        native = ctypes.CDLL(None, use_errno=True)
        native.realpath.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
        native.realpath.restype = ctypes.c_void_p
        native.free.argtypes = [ctypes.c_void_p]
        ptr = native.realpath(os.fsencode(alias), None)
        self.assertTrue(ptr, "native oracle unavailable")
        try:
            canonical = os.fsdecode(ctypes.string_at(ptr))
        finally:
            native.free(ptr)
        self.assertEqual(canonical, str(stored))
        settings = {"trust": {canonical: "trusted", str(alias): "untrusted"}}
        resolved = resolve_settings(self.request(settings), alias)
        self.assertEqual((resolved.trust, resolved.trust_key), ("trusted", canonical))

    def test_group_record_overrides_conflicting_member_settings(self):
        self.trust()
        self.put(self.root / "a/ALT.md", "a" * 10)
        self.put(self.root / "b/ALT.md", "b" * 10)
        self.put(self.root / "a/.codex/config.toml", "project_doc_max_bytes=2\n")
        self.put(self.root / "b/.codex/config.toml", "project_doc_max_bytes=3\n")
        group = {"id": "pair", "cwds": [str(self.root / "a"), str(self.root / "b")],
                 "effective_loader_settings": {"limit": 15, "fallback_names": ["ALT.md"], "root_markers": [], "trust": "trusted"}}
        proc, report = self.cli({"environment_groups": [group], "declared_bases": {}})
        self.assertIsNotNone(report, proc.stderr)
        self.assertTrue(report["groups"], "baseline has no modeled groups")
        self.assertEqual([r["project_included_bytes"] for r in report["groups"][0]["members"]], [10, 5])

    def test_input_fingerprint_unchanged_and_version_guard(self):
        before = hashlib.sha256((self.root / "AGENTS.md").read_bytes()).hexdigest()
        proc, report = self.cli(extra=["--cwd", str(self.root)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(report["chains"], "baseline reports no audit")
        self.assertEqual(hashlib.sha256((self.root / "AGENTS.md").read_bytes()).hexdigest(), before)
        source = (SOT / "scripts/md_improver.py").read_text()
        ast.parse(source, feature_version=(3, 9))
        env = {**os.environ}
        command = "import runpy,sys; sys.version_info=(3,10,0); runpy.run_path(sys.argv[1],run_name='__main__')"
        old = subprocess.run([sys.executable, "-c", command, str(SOT / "scripts/md_improver.py")], capture_output=True, text=True, env=env)
        self.assertEqual(old.returncode, 2)
        self.assertIn("Python 3.11", old.stderr)


if __name__ == "__main__":
    unittest.main()
