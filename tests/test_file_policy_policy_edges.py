"""Additional boundaries: unknown identity, changed aliases, evidence controls."""
from dataclasses import asdict
import copy
import json
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_references as fixtures
from discovery import _Content, _protected_content, ScopeRequest, scan, resolve_settings
from reporting import enrich_audit, report_hash, compare_reports
from md_improver import main
import test_file_policy_only as helper_tests


class PolicyEdgeTests(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    settings = helper_tests.MetadataOnlyTests.settings
    run_scan = helper_tests.MetadataOnlyTests.run_scan
    guard = helper_tests.MetadataOnlyTests.guard

    def test_unobservable_declaration_identity_blocks_readable_hardlink(self):
        target = self.put(self.root / "private/hold.md", "secret")
        alias = self.root / "public/alias.md"
        alias.parent.mkdir()
        os.link(target, alias)
        self.put(self.source, "[alias](public/alias.md)")
        chains = [fixtures.ReferenceTests.chain(self)]
        original_stat = Path.stat
        def metadata(path, *args, **kwargs):
            if path == target:
                raise PermissionError("synthetic metadata permission failure")
            return original_stat(path, *args, **kwargs)
        with self.guard(target), patch.object(Path, "stat", metadata):
            graph = fixtures.build_reference_graph(chains, context={
                "metadata_only_paths": [str(target)], "codex_home": self.home})
        self.assertTrue(graph["partial"])
        self.assertFalse(graph["nodes"])
        self.assertTrue(any(s["kind"] == "blocked_frontier" for s in graph["states"].values()))

    def test_cache_and_retargeted_declaration_keep_old_and_new_identities_blocked(self):
        old = self.put(self.root / "old.md", "old")
        new = self.put(self.root / "new.md", "new")
        declaration = self.root / "declared.md"
        declaration.symlink_to(old)
        reader = _Content()
        self.assertEqual(reader.read(old), b"old")
        _protected_content(ScopeRequest([self.root], self.home, self.root,
                                       self.settings([declaration])), reader)
        with self.assertRaises(PermissionError):
            reader.read(old)
        declaration.unlink()
        declaration.symlink_to(new)
        with self.guard(new), self.assertRaises(PermissionError):
            reader.read(new)
        with self.guard(old), self.assertRaises(PermissionError):
            reader.read(old)

    def test_missing_path_creation_is_protected_on_later_read(self):
        target = self.root / "later.md"
        reader = _protected_content(ScopeRequest([self.root], self.home, self.root,
                                                self.settings([target])))
        self.put(target, "later")
        alias = self.root / "alias.md"
        os.link(target, alias)
        with self.guard(target), self.assertRaises(PermissionError):
            reader.read(alias)

    def test_cyclic_declaration_does_not_crash_or_open_it(self):
        target = self.root / "cycle.md"
        target.symlink_to(target)
        self.put(self.source, "[cycle](cycle.md)")
        code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        self.assertTrue(audit["partial"])
        self.assertFalse(audit["graph"]["nodes"])
        row = audit["metadata_only_files"][0]
        self.assertEqual(row["status"], "unavailable")
        self.assertEqual(row["reason"], "unresolved_metadata_identity")
        self.assertIsNone(row["metadata_bytes"])

    def test_report_evidence_control_succeeds_without_policy_and_fails_with_policy(self):
        target = self.put(self.root / "hold.md", "secret")
        alias = self.root / "alias.md"
        os.link(target, alias)
        self.put(self.source, "[target](hold.md)")
        _, audit, _ = self.run_scan([], cwd=True)
        self.assertIsNotNone(audit)
        digest = hashlib.sha256(b"secret").hexdigest()
        # Use a real readable graph node and append an existing equivalent alias.
        node = next(n for n in audit["graph"]["nodes"].values() if str(target) in n["aliases"])
        node["aliases"].append(str(alias))
        assessment = {"schema_version": 1, "audit_sha256": report_hash(audit),
                      "reviewed_sources": [{"source": str(alias), "source_sha256": digest}]}
        result = enrich_audit(audit, assessment)
        self.assertIn(str(alias), result["reviewed_sources"])
        denied = copy.deepcopy(audit)
        denied["scope"]["settings"]["metadata_only_paths"] = [str(target)]
        assessment["audit_sha256"] = report_hash(denied)
        with self.guard(target), self.assertRaises(ValueError):
            enrich_audit(denied, assessment)

    def test_metadata_declarations_remain_separate_from_text_total(self):
        target = self.put(self.root / "hold.md", "123456789")
        self.put(self.source, "[hold](hold.md)\n[ok](ok.md)")
        self.put(self.root / "ok.md", "abc")
        _, audit, _ = self.run_scan([target], cwd=True)
        self.assertIsNotNone(audit)
        self.assertEqual(audit["reading_summary"]["unique_text_bytes"], 30)
        self.assertEqual(audit["metadata_only_files"][0]["metadata_bytes"], 9)
        self.assertEqual(audit["metadata_only_files"][0]["path"], str(target))
        self.assertEqual(audit["metadata_only_files"][0]["status"], "regular_file")
        self.assertEqual(audit["metadata_only_files"][0]["reason"], "metadata_only")
        states = [s for s in audit["graph"]["states"].values() if s["path"] == str(target)]
        self.assertTrue(states[0]["identity"])

    def test_group_policy_denial_is_not_a_modeled_runtime_failure(self):
        target = self.put(self.root / "AGENTS.override.md", "protected override")
        child = self.root / "child"
        self.put(child / "AGENTS.md", "permitted")
        (child / ".git").mkdir()
        settings = self.settings([target])
        settings["environment_groups"] = [{"id": "ordered", "cwds": [str(self.root), str(child)],
            "effective_loader_settings": {"limit": 32768, "root_markers": [".git"],
                                          "fallback_names": [], "trust": "trusted"}}]
        with self.guard(target):
            audit = scan(ScopeRequest([self.root], self.home, None, settings))
        group = audit["groups"][0]
        self.assertEqual(group["possible_outcomes"], ["unresolved"])
        self.assertTrue(all(m["modeled_loader_error"] is None for m in group["members"]))
        self.assertTrue(all(m["project_included_bytes"] is None for m in group["members"]))

    def test_git_trust_metadata_denial_preserves_unknown_trust(self):
        for slot in ("pointer", "gitdir", "commondir"):
            with self.subTest(slot=slot):
                main_root = self.base / slot / "main"
                linked = self.base / slot / "linked"
                admin = main_root / ".git/worktrees/linked"
                self.put(main_root / ".git/HEAD", "ref: refs/heads/main")
                self.put(linked / ".git", "gitdir: " + str(admin))
                self.put(admin / "gitdir", str(linked / ".git"))
                self.put(admin / "commondir", "../..")
                target = linked / ".git" if slot == "pointer" else admin / slot
                request = ScopeRequest([linked], self.home, linked,
                    {"metadata_only_paths": [str(target)], "trust": {str(main_root): "trusted"}})
                with self.guard(target):
                    value = asdict(resolve_settings(request, linked))
                self.assertEqual(value["trust"], "unknown")
                self.assertIn("trust:MetadataOnlyError", value["unresolved"])

    def test_broken_declaration_is_accepted_and_remains_excluded(self):
        target = self.root / "broken.md"
        target.symlink_to(self.root / "absent.md")
        self.put(self.source, "[broken](broken.md)")
        code, audit, _ = self.run_scan([target], cwd=True)
        self.assertEqual(code, 3)
        states = [s for s in audit["graph"]["states"].values() if s["path"] == str(target)]
        self.assertEqual(states[0]["kind"], "excluded_metadata_only")

    def test_secondary_resolutions_input_cannot_bypass_policy(self):
        target = self.put(self.base / "resolutions.json", "[]")
        settings = self.put(self.base / "settings.json", json.dumps(self.settings([target])))
        with self.guard(target):
            code = main(["scan", "--project", str(self.root), "--codex-home", str(self.home),
                         "--settings", str(settings), "--resolutions", str(target),
                         "--out", str(self.base / "denied-control-output")])
        self.assertEqual(code, 2)

    def test_secondary_assessment_input_cannot_bypass_persisted_policy(self):
        target = self.put(self.base / "assessment.json", "{}")
        _, audit, out = self.run_scan([target], cwd=True)
        self.assertIsNotNone(audit)
        with self.guard(target):
            code = main(["report", "--audit", str(out / "audit.json"),
                         "--assessment", str(target), "--out", str(self.base / "report")])
        self.assertEqual(code, 2)

    def test_empty_and_absent_declarations_are_comparable(self):
        _, audit, _ = self.run_scan([], cwd=True)
        self.assertIsNotNone(audit)
        legacy = copy.deepcopy(audit)
        legacy["scope"]["settings"].pop("metadata_only_paths")
        self.assertTrue(compare_reports(legacy, audit)["comparable"])

    def test_denied_global_override_keeps_readable_fallback_conditional(self):
        target = self.put(self.home / "AGENTS.override.md", "maybe nonempty")
        fallback = self.put(self.home / "AGENTS.md", "guidance line\n" * 101)
        with self.guard(target):
            _, audit, _ = self.run_scan([target], cwd=True)
        self.assertIsNotNone(audit)
        source = audit["chains"][0]["global_source"]
        self.assertEqual(source["state"], "metadata_only")
        self.assertIsNone(source["included_bytes"])
        nodes = audit["graph"]["nodes"].values()
        self.assertIn(str(fallback), {p for n in nodes for p in n["aliases"]})
        self.assertTrue(source["conditional_sources"][0]["condition"])
        self.assertFalse(any(c["path"] == str(fallback) and c["rule_id"] == "L-C9-TOC"
                             for c in audit["candidates"]))

    def test_zero_byte_global_override_can_select_fallback_by_metadata(self):
        target = self.put(self.home / "AGENTS.override.md", "")
        fallback = self.put(self.home / "AGENTS.md", "fallback")
        with self.guard(target):
            _, audit, _ = self.run_scan([target], cwd=True)
        self.assertIsNotNone(audit)
        self.assertEqual(audit["chains"][0]["global_source"]["path"], str(fallback))
        self.assertTrue(audit["partial"])

    @unittest.skipUnless(os.name == "posix" and os.geteuid() != 0,
                         "native search-permission denial needs unprivileged POSIX")
    def test_unresolved_identity_scan_and_group_finish_partial_without_runtime_failure(self):
        target = self.put(self.root / "private/hold.md", "secret")
        alias = self.root / "alias.md"
        os.link(target, alias)
        self.put(self.source, "[alias](alias.md)")
        child = self.root / "child"
        self.put(child / "AGENTS.md", "readable child")
        (child / ".git").mkdir()
        for grouped in (False, True):
            with self.subTest(grouped=grouped):
                settings = self.settings([target])
                if grouped:
                    settings["environment_groups"] = [{"id": "two", "cwds": [str(self.root), str(child)],
                        "effective_loader_settings": {"limit": 32768, "root_markers": [".git"],
                                                      "fallback_names": [], "trust": "trusted"}}]
                with self.guard(target), patch.object(self, "settings", return_value=settings):
                    target.parent.chmod(0)
                    try:
                        with self.assertRaises(PermissionError):
                            target.stat()
                        code, audit, out = self.run_scan([target], cwd=not grouped)
                    finally:
                        target.parent.chmod(0o700)
                self.assertEqual(code, 3)
                self.assertTrue(audit["partial"])
                self.assertFalse(audit["graph"]["nodes"])
                root_chain = next(c for c in audit["chains"] if c["cwd"] == str(self.root))
                self.assertEqual(root_chain["loader_outcome"], "unresolved")
                self.assertIsNone(root_chain["modeled_loader_error"])
                self.assertIsNone(root_chain["project_included_bytes"])
                self.assertEqual(root_chain["sources"][0]["read_error"], "MetadataIdentityError")
                self.assertEqual(root_chain["sources"][0]["read_reason"], "unresolved_metadata_identity")
                self.assertEqual(audit["metadata_only_files"][0]["status"], "unavailable")
                self.assertEqual(audit["metadata_only_files"][0]["reason"], "unresolved_metadata_identity")
                if grouped:
                    group = audit["groups"][0]
                    self.assertEqual(group["possible_outcomes"], ["unresolved"])
                    self.assertTrue(all(m["modeled_loader_error"] is None for m in group["members"]))
                    self.assertTrue(all(m["project_included_bytes"] is None for m in group["members"]))
                manifest = json.loads((out / "manifest.json").read_text())
                self.assertEqual(manifest["phase"], "finished")
                self.assertFalse(manifest["complete"])

    def test_reordered_duplicate_declarations_compare_as_same_set(self):
        _, audit, _ = self.run_scan([], cwd=True)
        self.assertIsNotNone(audit)
        before, after = copy.deepcopy(audit), copy.deepcopy(audit)
        a, b = str(self.root / "a.md"), str(self.root / "b.md")
        before["scope"]["settings"]["metadata_only_paths"] = [a, b]
        after["scope"]["settings"]["metadata_only_paths"] = [b, a, b]
        self.assertTrue(compare_reports(before, after)["comparable"])

    def test_unreached_regular_declaration_does_not_make_scan_partial(self):
        target = self.put(self.base / "unreached.md", "secret")
        with self.guard(target):
            code, audit, _ = self.run_scan([target], cwd=True)
        self.assertIsNotNone(audit)
        self.assertIn(code, (0, 1))
        self.assertFalse(audit["partial"])
        self.assertEqual(audit["metadata_only_files"][0]["status"], "regular_file")

    def test_persisted_metadata_shapes_are_validated_without_target_stat(self):
        _, audit, _ = self.run_scan([], cwd=True)
        self.assertIsNotNone(audit)
        for invalid in (None, 42, "bad", ["relative.md"]):
            with self.subTest(invalid=invalid):
                bad = copy.deepcopy(audit)
                bad["scope"]["settings"]["metadata_only_paths"] = invalid
                with self.assertRaises(ValueError):
                    compare_reports(audit, bad)
        bad = copy.deepcopy(audit)
        bad["metadata_only_files"] = [{"path": str(self.root / "gone.md"),
            "status": "regular_file", "reason": "metadata_only",
            "metadata_bytes": True, "physical_identity": [1, 2]}]
        with self.assertRaises(ValueError):
            compare_reports(audit, bad)
        archived = copy.deepcopy(audit)
        archived["scope"]["settings"]["metadata_only_paths"] = [str(self.root / "gone.md")]
        with patch.object(Path, "stat", side_effect=AssertionError("Historical comparison must not stat targets")):
            self.assertTrue(compare_reports(archived, archived)["comparable"])


if __name__ == "__main__":
    unittest.main()
