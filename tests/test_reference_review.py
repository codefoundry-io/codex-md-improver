"""Independent Task 2 review regressions, including interrupted replacement."""
import json
import os
from pathlib import Path
import signal
import unittest
from unittest.mock import patch
import test_references as fixtures


class ReferenceReviewTests(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    chain = fixtures.ReferenceTests.chain
    build = fixtures.ReferenceTests.build
    routes = fixtures.ReferenceTests.routes
    decision = fixtures.ReferenceTests.decision
    cli = fixtures.ReferenceTests.cli

    def test_alias_first_seen_as_cycle_can_expand_on_another_route(self):
        self.put(self.source, "[a](a/shared.md)\n[b](b/shared.md)\n")
        a = self.put(self.root / "a/shared.md", "[same](../b/shared.md)\n[leaf](leaf.md)\n")
        b = self.root / "b/shared.md"
        b.parent.mkdir()
        os.link(a, b)
        leaf_a = self.put(self.root / "a/leaf.md", "A")
        leaf_b = self.put(self.root / "b/leaf.md", "BB")
        graph = self.build()
        rows = self.routes(graph)
        self.assertEqual({r["terminal_path"] for r in rows if r["terminal_kind"] == "leaf"},
                         {str(leaf_a), str(leaf_b)})
        self.assertEqual(sum(r["terminal_kind"] == "cycle" for r in rows), 2)

    def test_cli_group_sources_and_dependencies_have_separate_scenarios(self):
        child = self.root / "child"
        source = self.put(child / "ALT.md", "[group dependency](missing.md)\n")
        group = {"id": "explicit", "cwds": [str(child)],
                 "effective_loader_settings": {"limit": 100, "root_markers": [],
                                               "fallback_names": ["ALT.md"], "trust": "trusted"}}
        settings = self.put(self.base / "settings.json", json.dumps({"environment_groups": [group]}))
        # Whole-project invocation permits this group's child cwd.
        import subprocess, sys
        out = self.base / "group-run"
        proc = subprocess.run([sys.executable, str(fixtures.SOT / "scripts/md_improver.py"), "scan",
            "--project", str(self.root), "--codex-home", str(self.home),
            "--settings", str(settings), "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        report = json.loads((out / "audit.json").read_text())
        member = report["groups"][0]["members"][0]
        self.assertNotIn(member["scenario_id"], {c["scenario_id"] for c in report["chains"]})
        rows = [json.loads(line) for line in (out / "routes.jsonl").read_text().splitlines()]
        selected = [r for r in rows if r["originating_instruction_file"] == str(source)]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["environment_group_id"], "explicit")
        self.assertEqual(selected[0]["project_included_bytes"], source.stat().st_size)
        self.assertEqual(selected[0]["terminal_kind"], "missing_target")

    def test_markdown_output_and_example_links_need_bound_non_read_decisions(self):
        self.put(self.source, "Write [report](result.md).\nExample: [sample][sample].\n[sample]: example.md\n")
        self.assertTrue(self.build()["partial"])
        graph = self.build(resolutions=[self.decision("result.md", "output"),
                                      self.decision("[sample][sample]", "example")])
        self.assertFalse(graph["partial"])
        self.assertEqual([e["classification"] for e in graph["occurrences"]], ["output", "example"])
        self.assertEqual({e["status"] for e in graph["occurrences"]}, {"non_read"})

    def test_resolved_skill_and_git_aliases_are_metadata_only(self):
        skill = self.put(self.base / "external/SKILL.md", "SHOULD_NOT_READ_SKILL")
        git = self.put(self.base / "external/.git/config", "SHOULD_NOT_READ_GIT")
        alias_skill, alias_git = self.root / "guide.md", self.root / "support.md"
        alias_skill.symlink_to(skill)
        alias_git.symlink_to(git)
        self.put(self.source, "[skill](guide.md)\n[git](support.md)\n")
        original = Path.read_bytes
        def read(path):
            self.assertNotIn(path.resolve(), (skill, git), "Excluded alias content was read")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            graph = self.build()
        self.assertEqual({r["terminal_kind"] for r in self.routes(graph)}, {"excluded_skill", "excluded_git"})

    def test_kill_during_manifest_refresh_preserves_previous_valid_receipt(self):
        self.put(self.source, "[a](a.md)\n[b](b.md)\n")
        self.put(self.root / "a.md", "a")
        self.put(self.root / "b.md", "b")
        code = "\n".join([
            "import sys,pathlib,os,signal",
            "sys.path.insert(0," + repr(str(fixtures.SOT / "scripts")) + ")",
            "import md_improver",
            "original_write, original_replace = pathlib.Path.write_text, os.replace",
            "counts = {'write': 0, 'replace': 0}",
            "def write(path, *args, **kwargs):",
            "    if path.name == 'manifest.json':",
            "        counts['write'] += 1",
            "        if counts['write'] == 4:",
            "            path.open('w').close()",
            "            os.kill(os.getpid(), signal.SIGKILL)",
            "    return original_write(path, *args, **kwargs)",
            "def replace(source, target, *args, **kwargs):",
            "    if pathlib.Path(target).name == 'manifest.json':",
            "        counts['replace'] += 1",
            "        if counts['replace'] == 4: os.kill(os.getpid(), signal.SIGKILL)",
            "    return original_replace(source, target, *args, **kwargs)",
            "pathlib.Path.write_text, os.replace = write, replace",
            "sys.exit(md_improver.main(sys.argv[1:]))"])
        proc, out = self.cli(code=code)
        self.assertEqual(proc.returncode, -signal.SIGKILL, proc.stderr)
        self.assertEqual(len((out / "routes.jsonl").read_text().splitlines()), 1)
        try:
            manifest = json.loads((out / "manifest.json").read_text())
        except (OSError, ValueError) as error:
            self.fail("Previously committed incomplete manifest was lost: " + str(error))
        self.assertFalse(manifest["complete"])


if __name__ == "__main__":
    unittest.main()
