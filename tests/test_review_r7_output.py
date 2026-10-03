"""Report coverage wording and regression-fixture portability contracts."""
import ast
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures
from reporting import render_audit


class ReportLimits(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put
    cli = fixtures.ReferenceTests.cli

    def test_route_cap_is_explicit_in_markdown_and_rerender(self):
        self.put(self.source, 'Read [A](a.md) and [B](b.md).\n')
        self.put(self.root / 'a.md', 'A')
        self.put(self.root / 'b.md', 'B')
        proc, out = self.cli(['--max-routes', '1'])
        self.assertEqual(proc.returncode, 3, proc.stderr)
        audit = json.loads((out / 'audit.json').read_text())
        self.assertTrue(audit['route_limit_reached'])
        text = (out / 'audit.md').read_text()
        self.assertNotIn('Complete route stream', text)
        self.assertIn('Route stream truncated by --max-routes', text)
        self.assertIn('Route stream truncated by --max-routes', render_audit(audit))

    def test_complete_stream_control(self):
        self.put(self.source, 'Read [A](a.md).\n')
        self.put(self.root / 'a.md', 'A')
        proc, out = self.cli()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('Complete route stream: routes.jsonl', (out / 'audit.md').read_text())
        self.assertNotIn('Route stream truncated', (out / 'audit.md').read_text())

    def test_r6_project_bindings_follow_selected_test_location(self):
        # Structural portability check of the actual PROJECT binding, evaluated
        # with a different __file__; no copied skill is executed or admitted.
        for path in sorted((PROJECT / 'tests').glob('test_review_r6*.py')):
            with self.subTest(file=path.name):
                tree = ast.parse(path.read_text())
                assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'PROJECT' for t in n.targets))
                selected = self.base / 'selected-checkout'
                actual = eval(compile(ast.Expression(assignment.value), str(path), 'eval'),
                              {'Path': Path, '__file__': str(selected / 'tests' / path.name)})
                self.assertEqual(actual, selected)
