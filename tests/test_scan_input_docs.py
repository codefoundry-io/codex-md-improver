"""Execute shipped scan-input examples against the canonical analyzer."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
sys.path.insert(0, str(PROJECT / 'skills/codex-md-improver/scripts'))
import test_references as fixtures
import md_improver


class ScanInputDocumentation(unittest.TestCase):
    setUp = fixtures.ReferenceTests.setUp
    put = fixtures.ReferenceTests.put

    def example(self, heading):
        path = PROJECT / 'skills/codex-md-improver/references/assessment-format.md'
        text = path.read_text()
        section = text.partition('## ' + heading + '\n')[2].partition('\n## ')[0]
        match = re.search(r'(?ms)^' + chr(96) * 3 + r'json\n(.*?)^' + chr(96) * 3, section)
        self.assertIsNotNone(match, 'Shipped scan contract needs an executable JSON example: ' + heading)
        return match[1]

    def test_documented_settings_and_resolution_examples_drive_bounded_rescan(self):
        self.put(self.source, 'Use ' + chr(96) + 'guide.md' + chr(96) + ' for implementation conventions.\n')
        guide = self.put(self.root / 'guide.md', 'plain guidance')
        settings = self.example('Scan settings input').replace('/absolute/project/AGENTS.md', str(self.source))
        settings_path = self.put(self.base / 'settings.json', settings)
        args = ['scan', '--project', str(self.root), '--cwd', str(self.root),
                '--codex-home', str(self.home), '--settings', str(settings_path)]
        first = self.base / 'first'
        self.assertEqual(md_improver.main([*args, '--out', str(first)]), 3)
        first_report = json.loads((first / 'audit.json').read_text())
        effective = first_report['chains'][0]['settings']
        self.assertEqual(effective['limit'], 40000)
        self.assertEqual(effective['fallback_names'], ['RULES.md'])
        occurrence = first_report['graph']['occurrences'][0]
        self.assertEqual(occurrence['classification'], 'uncertain')
        resolution = self.example('Scan occurrence resolutions')
        resolution = resolution.replace('/absolute/project/AGENTS.md', str(self.source))
        resolution = resolution.replace('<sha256 of original source bytes>',
                                        hashlib.sha256(self.source.read_bytes()).hexdigest())
        resolutions = json.loads(resolution)
        self.assertEqual(resolutions[0]['span'], occurrence['span'])
        self.assertEqual(resolutions[0]['text'], occurrence['text'])
        resolution_path = self.put(self.base / 'resolutions.json', json.dumps(resolutions))
        second = self.base / 'second'
        self.assertIn(md_improver.main([*args, '--resolutions', str(resolution_path),
                                       '--out', str(second)]), (0, 1))
        report = json.loads((second / 'audit.json').read_text())
        self.assertFalse(report['partial'])
        rows = [json.loads(line) for line in (second / 'routes.jsonl').read_text().splitlines()]
        self.assertIn(str(guide), {row['terminal_path'] for row in rows})


if __name__ == '__main__':
    unittest.main()
