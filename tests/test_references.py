"""Synthetic reference routes and output lifecycle, with no target execution."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SOT = Path(__file__).resolve().parents[1] / "skills/codex-md-improver"
sys.path.insert(0, str(SOT / "scripts"))
from references import build_reference_graph, iter_terminal_paths, summarize_reading_paths


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="references-", dir=os.environ.get("CODEX_MD_TEST_TMP"))
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root, self.home = self.base / "project", self.base / "home"
        self.root.mkdir()
        self.home.mkdir()
        self.source = self.put(self.root / "AGENTS.md", "instructions")

    def put(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text if isinstance(text, bytes) else text.encode())
        return path

    def chain(self, cwd=None, source=None, scenario="one", global_path=None):
        source = source or self.source
        data = source.read_bytes()
        return {"scenario_id": scenario, "cwd": str(cwd or self.root),
                "scenario_project_root": str(self.root), "inventory_root": str(self.root),
                "sources": [{"path": str(source), "sha256": hashlib.sha256(data).hexdigest(),
                             "original_bytes": len(data)}], "scope_sources": [],
                "global_source": {"path": str(global_path) if global_path else None,
                                  "original_bytes": global_path.stat().st_size if global_path else 0},
                "project_original_bytes": len(data), "project_included_bytes": len(data)}

    def build(self, chains=None, bases=None, resolutions=None, **context):
        self.chains = chains or [self.chain()]
        return build_reference_graph(self.chains, bases or {}, resolutions or [],
                                     context={"codex_home": self.home, "user_home": self.home, **context})

    def routes(self, graph):
        return [row for chain in self.chains for row in iter_terminal_paths(graph, chain)]

    def decision(self, text, classification="read_dependency", **fields):
        source = self.source.read_text()
        start = source.index(text)
        return {"source": str(self.source), "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                "span": [start, start + len(text)], "text": text, "classification": classification, **fields}

    def cli(self, extra=(), out=None, code=None):
        out = out or self.base / ("run-" + str(len(list(self.base.glob("run-*")))))
        argv = ["scan", "--project", str(self.root), "--cwd", str(self.root),
                "--codex-home", str(self.home), "--out", str(out), *extra]
        prefix = [sys.executable, "-c", code] if code else [sys.executable, str(SOT / "scripts/md_improver.py")]
        result = subprocess.run(prefix + argv, text=True, capture_output=True, timeout=10)
        return result, out

    def test_markdown_reference_links_spaces_suffixes_and_url(self):
        self.put(self.source, "[guide](<docs/한 글.md#part>)\n[other][ref]\n[ref]: docs/b.md:12\n[web](https://example.org/a)\n")
        self.put(self.root / "docs/한 글.md", "first")
        self.put(self.root / "docs/b.md", "second")
        graph = self.build()
        rows = self.routes(graph)
        self.assertEqual({Path(r["terminal_path"]).name for r in rows if r["terminal_kind"] == "leaf"}, {"한 글.md", "b.md"})
        self.assertTrue(any(e["status"] == "url" for e in graph["occurrences"]))
        self.assertFalse(graph["partial"])

    def test_ambiguous_plain_base_never_guessed_from_existence(self):
        self.put(self.source, "Read `docs/a.md` when building.\n")
        self.put(self.root / "docs/a.md", "only existing target")
        cwd = self.root / "sub"
        cwd.mkdir()
        graph = self.build([self.chain(cwd)])
        self.assertTrue(graph["partial"])
        edge = graph["occurrences"][0]
        self.assertEqual(edge["status"], "unresolved")
        self.assertGreaterEqual(len(edge["alternatives"]), 2)
        self.assertFalse(any(n.get("text") == "only existing target" for n in graph["nodes"].values()))

    def test_table_plain_paths_and_declared_document_base(self):
        self.put(self.source, "| Trigger | Read |\n| build | docs/a.md |\nRead docs/b.md when testing.\n")
        self.put(self.root / "docs/a.md", "A")
        self.put(self.root / "docs/b.md", "BB")
        graph = self.build(bases={str(self.source): {"kind": "document_dir"}})
        self.assertEqual({Path(r["terminal_path"]).name for r in self.routes(graph)}, {"a.md", "b.md"})
        self.assertTrue(all(e["condition"] for e in graph["occurrences"]))

    def test_nonread_candidates_and_code_evidence_do_not_recurse(self):
        self.put(self.source, "Write output to `result.md`.\nExample: `example.md`.\nRead [code](code.py).\n")
        self.put(self.root / "code.py", 'path = "secret.md"\n')
        self.put(self.root / "secret.md", "must not be reached")
        self.assertTrue(self.build()["partial"])
        graph = self.build(resolutions=[self.decision("result.md", "output"),
                                      self.decision("example.md", "example")])
        self.assertFalse(graph["partial"])
        classes = {e["classification"] for e in graph["occurrences"]}
        self.assertTrue({"output", "example", "read_dependency"}.issubset(classes))
        self.assertEqual([Path(r["terminal_path"]).name for r in self.routes(graph)], ["code.py"])

    def test_resolution_dismissal_and_stale_source(self):
        self.put(self.source, "Possible `missing.md` location.\n")
        self.assertTrue(self.build()["partial"])
        decision = self.decision("missing.md", "informational")
        graph = self.build(resolutions=[decision])
        self.assertFalse(graph["partial"])
        self.assertEqual(graph["occurrences"][0]["classification"], "informational")
        decision["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.build(resolutions=[decision])

    def test_added_occurrence_is_bound_to_exact_span(self):
        self.put(self.source, "Consult the blue book.\n")
        target = self.put(self.root / "manual.md", "manual")
        decision = self.decision("the blue book", target="manual.md", base={"kind": "document_dir"})
        graph = self.build(resolutions=[decision])
        self.assertEqual([r["terminal_path"] for r in self.routes(graph)], [str(target)])
        decision["text"] = "wrong span"
        with self.assertRaises(ValueError):
            self.build(resolutions=[decision])

    def test_scenario_specific_resolution_and_contradiction(self):
        self.put(self.source, "Maybe `missing.md`.\n")
        decision = self.decision("missing.md", "output", scenario_id="a")
        graph = self.build([self.chain(scenario="a"), self.chain(scenario="b")], resolutions=[decision])
        statuses = {e["scenario_id"]: e["status"] for e in graph["occurrences"]}
        self.assertEqual(statuses, {"a": "non_read", "b": "unresolved"})
        decision["target"] = "somewhere.md"
        with self.assertRaises(ValueError):
            self.build(resolutions=[decision])

    def test_physical_alias_content_cached_but_relative_meanings_preserved(self):
        self.put(self.source, "[A](a/shared.md)\n[B](b/shared.md)\n")
        physical = self.put(self.root / "a/shared.md", "[leaf](leaf.md)")
        alias = self.root / "b/shared.md"
        alias.parent.mkdir()
        os.link(physical, alias)
        self.put(self.root / "a/leaf.md", "A")
        self.put(self.root / "b/leaf.md", "BBB")
        original = Path.read_bytes
        reads = []
        def read(path):
            if path in (physical, alias):
                reads.append(path)
            return original(path)
        chains = [self.chain()]
        with patch.object(Path, "read_bytes", read):
            graph = self.build(chains)
        self.assertEqual(len(reads), 1)
        self.assertEqual({r["terminal_path"] for r in self.routes(graph)},
                         {str(self.root / "a/leaf.md"), str(self.root / "b/leaf.md")})

    def test_global_project_and_sibling_cwd_bases_keep_scenarios(self):
        global_path = self.put(self.home / "AGENTS.md", "Read `guide.md`.\n")
        a, b = self.root / "a", self.root / "b"
        self.put(a / "guide.md", "a" * 10240)
        self.put(b / "guide.md", "b" * 51200)
        chains = [self.chain(a, scenario="a", global_path=global_path), self.chain(b, scenario="b", global_path=global_path)]
        bases = {str(global_path): {"kind": "scenario_cwd"}}
        graph = self.build(chains, bases)
        rows = [r for r in self.routes(graph) if r["originating_instruction_file"] == str(global_path)]
        self.assertEqual({r["scenario_id"]: r["terminal_bytes"] for r in rows}, {"a": 10240, "b": 51200})
        self.assertEqual(len({r["cwd"] for r in rows}), 2)
        for chain, root in zip(chains, (a, b)):
            chain["scenario_project_root"] = str(root)
        bases[str(global_path)] = {"kind": "scenario_project_root"}
        graph = self.build(chains, bases)
        self.assertEqual(len([r for r in self.routes(graph) if r["terminal_bytes"] in (10240, 51200)]), 2)

    def test_absolute_tilde_placeholders_globs_and_unknown_variables(self):
        absolute = self.put(self.base / "absolute.md", "A")
        self.put(self.home / "home.md", "B")
        self.put(self.root / "docs/a.md", "C")
        self.put(self.root / "docs/b.md", "D")
        self.put(self.source, "[a](" + str(absolute) + ")\n[b](~/home.md)\n[c](${PROJECT_ROOT}/docs/*.md)\n[d]($MYSTERY/a.md)\n")
        with patch.object(Path, "home", return_value=self.home):
            graph = self.build()
        self.assertEqual(len([r for r in self.routes(graph) if r["terminal_kind"] == "leaf"]), 4)
        self.assertTrue(graph["partial"])
        self.assertTrue(any(e["status"] == "unresolved" for e in graph["occurrences"]))

    def test_each_terminal_path_has_its_own_total(self):
        head = "[shared](shared.md)\n"
        self.put(self.source, head + "x" * (1000 - len(head)))
        links = "[A](a.md)\n[B](b.md)\n"
        self.put(self.root / "shared.md", links + "x" * (200 - len(links)))
        self.put(self.root / "a.md", "a" * 300)
        self.put(self.root / "b.md", "b" * 400)
        graph = self.build()
        self.assertEqual(sorted(r["route_original_bytes"] for r in self.routes(graph)), [1500, 1600])
        self.assertEqual(summarize_reading_paths(graph)["unique_text_bytes"], 1900)
        self.assertEqual(self.chains[0]["project_included_bytes"], 1000)

    def test_shared_leaf_keeps_both_routes_and_loaded_source_not_double_counted(self):
        self.put(self.source, "[A](a.md)\n[B](b.md)\n")
        self.put(self.root / "a.md", "[shared](shared.md)")
        self.put(self.root / "b.md", "[shared](shared.md)")
        self.put(self.root / "shared.md", "[root](AGENTS.md)")
        graph = self.build()
        rows = self.routes(graph)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["terminal_kind"] for r in rows}, {"cycle"})
        for row in rows:
            self.assertEqual(row["route_original_bytes"], sum(Path(p).stat().st_size for p in set(row["route"])))

    def test_denied_subtree_preserves_readable_sibling_report(self):
        self.put(self.source, "[docs](docs/)\n")
        denied = self.root / "docs/a-denied"
        denied.mkdir(parents=True)
        self.put(self.root / "docs/z.md", "readable")
        original = Path.iterdir
        def entries(path):
            if path == denied:
                raise PermissionError("synthetic")
            return original(path)
        with patch.object(Path, "iterdir", entries):
            graph = self.build()
        rows = self.routes(graph)
        self.assertEqual({r["terminal_kind"] for r in rows}, {"blocked_frontier", "leaf"})
        blocked = next(r for r in rows if r["terminal_kind"] == "blocked_frontier")
        self.assertIsNone(blocked["terminal_bytes"])
        self.assertTrue(blocked["lower_bound"])
        self.assertTrue(graph["partial"])

    def test_directory_subtotal_200_files_and_empty_directory(self):
        self.put(self.source, "[docs](docs/)\n[empty](empty/)\n")
        for index in range(200):
            self.put(self.root / "docs" / (str(index) + ".md"), "x" * 5120)
        (self.root / "empty").mkdir()
        graph = self.build()
        self.assertEqual(graph["directory_totals"].get(str(self.root / "docs")), 1024000)
        self.assertEqual(len(self.routes(graph)), 201)
        self.assertTrue(any(r["terminal_kind"] == "empty_directory" for r in self.routes(graph)))

    def test_skill_boundaries_and_explicit_support_file(self):
        self.put(self.source, "[folder](skill/)\n[entry](skill/SKILL.md)\n[support](skill/helper.md)\n")
        skill = self.put(self.root / "skill/SKILL.md", "DO NOT READ ME")
        support = self.put(self.root / "skill/helper.md", "related guidance")
        original = Path.read_bytes
        def read(path):
            self.assertNotEqual(path, skill, "Existing SKILL.md must not be read")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            graph = self.build()
        rows = self.routes(graph)
        self.assertEqual(sum(r["terminal_kind"] == "excluded_skill" for r in rows), 2)
        self.assertIn(str(support), [r["terminal_path"] for r in rows])

    def test_implicit_git_boundary_is_complete_explicit_storage_is_limited(self):
        self.put(self.source, "[working](working/)\n")
        self.put(self.root / "working/.git", "gitdir: ../store\n")
        self.put(self.root / "working/guide.md", "guide")
        graph = self.build()
        self.assertFalse(graph["partial"])
        self.assertTrue(any(b["kind"] == "git_administration" for b in graph["boundaries"]))
        self.put(self.source, "[storage](working/.git)\n")
        graph = self.build()
        self.assertTrue(graph["partial"])
        self.assertEqual(self.routes(graph)[0]["terminal_kind"], "excluded_git")

    def test_binary_undecodable_special_missing_and_directory_cycle(self):
        self.put(self.source, "[binary](bin.dat)\n[text](bad.md)\n[fifo](pipe)\n[missing](gone.md)\n[dir](docs/)\n")
        self.put(self.root / "bin.dat", b"\0binary")
        self.put(self.root / "bad.md", b"\xff")
        os.mkfifo(self.root / "pipe")
        (self.root / "docs").mkdir()
        (self.root / "docs/cycle").symlink_to(self.root / "docs", target_is_directory=True)
        graph = self.build()
        self.assertEqual({r["terminal_kind"] for r in self.routes(graph)},
                         {"binary", "undecodable", "special_file", "missing_target", "cycle"})
        self.assertTrue(graph["partial"])

    def test_changed_during_read_remains_local_frontier(self):
        self.put(self.source, "[changing](changing.md)\n[good](good.md)\n")
        changing = self.put(self.root / "changing.md", "before")
        self.put(self.root / "good.md", "good")
        original = Path.read_bytes
        def read(path):
            data = original(path)
            if path == changing:
                path.write_text("different length after read")
            return data
        with patch.object(Path, "read_bytes", read):
            graph = self.build()
        self.assertEqual({r["terminal_kind"] for r in self.routes(graph)}, {"changed_during_read", "leaf"})
        self.assertTrue(graph["partial"])

    def test_known_sensitive_paths_and_hardlink_aliases_are_never_read(self):
        paths = [".aws/credentials", ".codex/auth.json", ".ssh/id_rsa", ".ssh/id_dsa", ".ssh/id_ecdsa",
                 ".ssh/id_ed25519", ".netrc", ".git-credentials", ".pypirc", ".npmrc", ".config/gh/hosts.yml"]
        protected = [self.put(self.home / p, "SENTINEL_PRIVATE_VALUE") for p in paths]
        protected.append(self.put(self.home / "auth.json", "CUSTOM_CODEX_HOME_VALUE"))
        alias = self.root / "alias.txt"
        os.link(protected[0], alias)
        symlink = self.root / "symlink.txt"
        symlink.symlink_to(protected[-1])
        self.put(self.source, "\n".join("[s](" + str(p) + ")" for p in [*protected, alias, symlink]))
        self.chains = [self.chain()]
        original = Path.read_bytes
        identities = {(p.stat().st_dev, p.stat().st_ino) for p in protected}
        def read(path):
            info = path.stat()
            self.assertNotIn((info.st_dev, info.st_ino), identities, "Known credentials were read")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            graph = self.build(self.chains)
        self.assertEqual(len(self.routes(graph)), len(protected) + 2)
        self.assertEqual({r["terminal_kind"] for r in self.routes(graph)}, {"excluded_sensitive"})
        self.assertNotIn("SENTINEL_PRIVATE_VALUE", repr(graph))

    def test_cli_routes_cap_and_resolution_dismissal(self):
        self.put(self.source, "[A](a.md)\n[B](b.md)\n")
        self.put(self.root / "a.md", "A")
        self.put(self.root / "b.md", "B")
        proc, out = self.cli(["--max-routes", "1"])
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(len((out / "routes.jsonl").read_text().splitlines()), 1)
        self.assertFalse(json.loads((out / "manifest.json").read_text())["complete"])
        self.put(self.source, "Potential `result.md`.\n")
        proc, _ = self.cli()
        self.assertEqual(proc.returncode, 3, proc.stderr)
        resolution = self.put(self.base / "decisions.json", json.dumps([self.decision("result.md", "output")]))
        proc, out = self.cli(["--resolutions", str(resolution)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads((out / "audit.json").read_text())["graph"]["occurrences"][0]["classification"], "output")

    def test_output_late_overlap_prior_reports_and_input_fingerprint(self):
        shared = self.base / "shared"
        prior = self.put(shared / "older/audit.md", "prior ordinary document")
        self.put(self.source, "[shared](" + str(shared) + ")\n")
        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        proc, out = self.cli(out=shared / "new-run")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertTrue((out / "manifest.json").exists())
        proc, out = self.cli(["--allow-output-in-target"], out=shared / "allowed-run")
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        rows = [json.loads(line) for line in (out / "routes.jsonl").read_text().splitlines()]
        self.assertIn(str(prior), [r["terminal_path"] for r in rows])
        self.assertFalse(any(str(out) in r["route"] for r in rows))
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), before)

    def test_direct_reference_to_owned_output_refuses_even_with_opt_in(self):
        out = self.base / "owned"
        self.put(self.source, "[output](" + str(out / "manifest.json") + ")\n")
        proc, actual = self.cli(["--allow-output-in-target"], out=out)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertTrue((actual / "manifest.json").exists())

    def test_no_readable_input_produces_coverage_receipt(self):
        self.source.unlink()
        proc, out = self.cli()
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertTrue((out / "audit.json").exists())
        self.assertFalse(json.loads((out / "audit.json").read_text())["semantic_review_complete"])

    def test_catchable_signal_keeps_incomplete_manifest(self):
        code = ("import sys,os,signal; sys.path.insert(0," + repr(str(SOT / "scripts")) + "); "
                "import discovery,md_improver; "
                "discovery.scan=lambda *a,**k: os.kill(os.getpid(),signal.SIGTERM); "
                "sys.exit(md_improver.main(sys.argv[1:]))")
        proc, out = self.cli(code=code)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertFalse(json.loads((out / "manifest.json").read_text())["complete"])

    def test_killed_process_leaves_manifest_started_before_traversal(self):
        out, marker = self.base / "killed", self.base / "ready"
        code = ("import sys,time,pathlib; sys.path.insert(0," + repr(str(SOT / "scripts")) + "); "
                "import discovery,md_improver; "
                "discovery.scan=lambda *a,**k: (pathlib.Path(" + repr(str(marker)) + ").write_text('ready'),time.sleep(20)); "
                "sys.exit(md_improver.main(sys.argv[1:]))")
        process = subprocess.Popen([sys.executable, "-c", code, "scan", "--project", str(self.root),
                                    "--codex-home", str(self.home), "--out", str(out)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(marker.exists(), "Test child never entered traversal")
            self.assertTrue((out / "manifest.json").exists(), "Manifest must precede traversal")
            self.assertFalse(json.loads((out / "manifest.json").read_text())["complete"])
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)
        self.assertEqual(process.returncode, -signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
