"""Task 2 contract-preflight cases that distinguish identity and lifecycle edges."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import test_references as fixtures


class ReferenceEdgeTests(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    decision = fixtures.ReferenceTests.decision
    cli = fixtures.ReferenceTests.cli

    def test_duplicate_unicode_occurrence_resolution_is_local(self):
        self.put(self.source, "한국어 설명: `missing.md` 그리고 `missing.md`.\n")
        decision = self.decision("missing.md", "informational")
        graph = self.build(resolutions=[decision])
        edges = graph["occurrences"]
        self.assertEqual([e["status"] for e in edges], ["non_read", "unresolved"])
        self.assertEqual(edges[0]["span"], decision["span"])
        self.assertTrue(graph["partial"])

    def test_alias_specific_resolution_does_not_dismiss_other_alias(self):
        self.put(self.source, "[A](a/shared.md)\n[B](b/shared.md)\n")
        a = self.put(self.root / "a/shared.md", "Possible `target.md`.\n")
        b = self.root / "b/shared.md"
        b.parent.mkdir()
        os.link(a, b)
        text = a.read_text()
        start = text.index("target.md")
        decision = {"source": str(a), "source_sha256": hashlib.sha256(a.read_bytes()).hexdigest(),
                    "span": [start, start + 9], "text": "target.md", "classification": "informational"}
        graph = self.build(resolutions=[decision])
        self.assertEqual({e["source"]: e["status"] for e in graph["occurrences"] if e["target_text"] == "target.md"},
                         {str(a): "non_read", str(b): "unresolved"})

    def test_two_scenarios_share_global_and_target_bytes_without_losing_routes(self):
        global_path = self.put(self.home / "AGENTS.md", "Read `guide.md`.\n")
        target = self.put(self.root / "guide.md", "shared")
        a, b = self.root / "a", self.root / "b"
        a.mkdir(); b.mkdir()
        chains = [self.chain(a, scenario="a", global_path=global_path), self.chain(b, scenario="b", global_path=global_path)]
        original, reads = Path.read_bytes, []
        def read(path):
            reads.append(path)
            return original(path)
        with patch.object(Path, "read_bytes", read):
            graph = self.build(chains, {str(global_path): {"kind": "scenario_project_root"}})
        self.assertEqual(reads.count(global_path), 1)
        self.assertEqual(reads.count(target), 1)
        rows = [r for r in self.routes(graph) if r["terminal_path"] == str(target)]
        self.assertEqual({r["scenario_id"] for r in rows}, {"a", "b"})

    def test_other_loaded_source_is_not_counted_twice(self):
        self.put(self.source, "[loaded](nested/AGENTS.md)\n")
        other = self.put(self.root / "nested/AGENTS.md", "[leaf](leaf.md)\n")
        leaf = self.put(self.root / "nested/leaf.md", "leaf")
        chain = self.chain()
        chain["sources"].append({"path": str(other), "original_bytes": other.stat().st_size})
        chain["project_original_bytes"] += other.stat().st_size
        graph = self.build([chain])
        rows = self.routes(graph)
        expected = sum(p.stat().st_size for p in (self.source, other, leaf))
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["route_original_bytes"] for r in rows}, {expected})

    def test_nested_skill_and_explicit_code_read_resolution(self):
        self.put(self.source, "[tree](docs/)\n[code](code.py)\n")
        self.put(self.root / "docs/skill/SKILL.md", "excluded")
        self.put(self.root / "docs/skill/hidden.md", "hidden")
        self.put(self.root / "docs/readable.md", "readable")
        code = self.put(self.root / "code.py", 'value = "target.md"\n')
        target = self.put(self.root / "target.md", "resolved code evidence")
        start = code.read_text().index("target.md")
        resolution = {"source": str(code), "source_sha256": hashlib.sha256(code.read_bytes()).hexdigest(),
                      "span": [start, start + 9], "text": "target.md", "classification": "read_dependency",
                      "base": {"kind": "document_dir"}, "target": "target.md"}
        graph = self.build(resolutions=[resolution])
        rows = self.routes(graph)
        self.assertIn(str(target), [r["terminal_path"] for r in rows])
        self.assertTrue(any(r["terminal_kind"] == "excluded_skill" for r in rows))
        self.assertNotIn(str(self.root / "docs/skill/hidden.md"), [r["terminal_path"] for r in rows])

    def test_cli_partial_read_preserves_rows_and_sensitive_frontier(self):
        bad = self.put(self.root / "bad.md", "blocked")
        self.put(self.root / "good.md", "good")
        secret = self.put(self.home / "auth.json", "SECRET_VALUE")
        self.put(self.source, "[bad](bad.md)\n[good](good.md)\n[auth](" + str(secret) + ")\n")
        code = "\n".join(["import sys,pathlib", "sys.path.insert(0," + repr(str(fixtures.SOT / "scripts")) + ")",
            "import md_improver", "original = pathlib.Path.read_bytes", "def read(path):",
            "    if str(path) == " + repr(str(bad)) + ": raise PermissionError('synthetic')",
            "    return original(path)", "pathlib.Path.read_bytes = read", "sys.exit(md_improver.main(sys.argv[1:]))"])
        proc, out = self.cli(code=code)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        audit = json.loads((out / "audit.json").read_text())
        self.assertTrue(audit["partial"])
        rows = [json.loads(line) for line in (out / "routes.jsonl").read_text().splitlines()]
        self.assertEqual({r["terminal_kind"] for r in rows}, {"blocked_frontier", "leaf", "excluded_sensitive"})
        self.assertNotIn("SECRET_VALUE", (out / "audit.json").read_text())

    def stream_code(self, action):
        return "\n".join(["import sys,time,pathlib", "sys.path.insert(0," + repr(str(fixtures.SOT / "scripts")) + ")",
            "import references,md_improver", "original = references.iter_terminal_paths", "def interrupted(*args):",
            "    for row in original(*args):", "        yield row", *["        " + line for line in action],
            "references.iter_terminal_paths = interrupted", "sys.exit(md_improver.main(sys.argv[1:]))"])

    def test_catchable_interrupt_preserves_flushed_route_prefix(self):
        self.put(self.source, "[a](a.md)\n[b](b.md)\n")
        self.put(self.root / "a.md", "a"); self.put(self.root / "b.md", "b")
        proc, out = self.cli(code=self.stream_code(["raise KeyboardInterrupt()"]))
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(len((out / "routes.jsonl").read_text().splitlines()), 1)
        self.assertFalse(json.loads((out / "manifest.json").read_text())["complete"])

    def test_kill_preserves_flushed_route_prefix(self):
        self.put(self.source, "[a](a.md)\n[b](b.md)\n")
        self.put(self.root / "a.md", "a"); self.put(self.root / "b.md", "b")
        out, marker = self.base / "killed-stream", self.base / "stream-ready"
        code = self.stream_code(["pathlib.Path(" + repr(str(marker)) + ").write_text('ready')", "time.sleep(20)"])
        proc = subprocess.Popen([sys.executable, "-c", code, "scan", "--project", str(self.root), "--cwd", str(self.root),
                                 "--codex-home", str(self.home), "--out", str(out)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() and proc.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(marker.exists(), "No committed stream prefix")
            self.assertEqual(len((out / "routes.jsonl").read_text().splitlines()), 1)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.communicate(timeout=5)
        self.assertEqual(proc.returncode, -signal.SIGKILL)
        self.assertFalse(json.loads((out / "manifest.json").read_text())["complete"])


if __name__ == "__main__":
    unittest.main()
