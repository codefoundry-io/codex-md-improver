"""Public persisted-report fixtures for reading-evidence regressions."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

SOT = Path(__file__).resolve().parents[1] / "skills/codex-md-improver"
sys.path.insert(0, str(SOT / "scripts"))
from references import build_reference_graph, summarize_reading_paths
from reporting import render_audit


class ReadingReportRegressionTests(unittest.TestCase):
    def setUp(self):
        scratch = os.environ.get("CODEX_MD_TEST_TMP")
        self.temp = tempfile.TemporaryDirectory(prefix="reading-report-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "project"
        self.home = self.base / "home"
        self.root.mkdir()
        self.home.mkdir()
        self.source = self.root / "AGENTS.md"

    def put(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def source_text(self, prefix):
        # Fixed ASCII byte count; filler creates no additional references.
        self.put("AGENTS.md", prefix + "x" * (137 - len(prefix.encode("utf-8"))))

    def chain(self, scenario="fixture", included=113, cwd=None):
        data = self.source.read_bytes()
        return {"scenario_id": scenario, "cwd": str(cwd or self.root),
                "scenario_project_root": str(self.root), "inventory_root": str(self.root),
                "sources": [{"path": str(self.source), "original_bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest()}],
                "scope_sources": [], "global_source": {"path": None, "original_bytes": 0},
                "project_original_bytes": len(data), "project_included_bytes": included}

    def report(self, chains):
        graph = build_reference_graph(chains, context={"codex_home": self.home, "user_home": self.home})
        summary = summarize_reading_paths(graph)
        graph = {key: value for key, value in graph.items() if not key.startswith("_")}
        return {"schema_version": 1, "chains": chains, "groups": [], "graph": graph,
                "reading_summary": summary, "inventory_complete": True,
                "text_read_complete": summary["text_read_complete"],
                "semantic_review_complete": False, "partial": summary["partial"],
                "assessment": "unassessed", "exit_code": 3 if summary["partial"] else 0}
