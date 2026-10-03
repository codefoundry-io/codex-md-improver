"""UTF-8 JSON input must preserve Unicode under an actual Latin-1 file locale."""
import codecs
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / 'skills/codex-md-improver/scripts/md_improver.py'
sys.path.insert(0, str(PROJECT / 'tests'))
import test_references as fixtures

METADATA = '''import codecs, json, locale, sys
try:
    active = locale.setlocale(locale.LC_ALL, "")
    preferred = locale.getpreferredencoding(False)
    print(json.dumps({"active": active, "preferred": preferred,
                      "codec": codecs.lookup(preferred).name,
                      "utf8_mode": sys.flags.utf8_mode,
                      "filesystem": sys.getfilesystemencoding()}))
except (locale.Error, LookupError) as error:
    print(json.dumps({"unsupported": str(error)}))
'''


class JsonInputLocale(unittest.TestCase):
    # Delegate helpers only. Fixture cleanup and CODEX_MD_TEST_TMP stay intact.
    put = fixtures.ReferenceTests.put

    def setUp(self):
        fixtures.ReferenceTests.setUp(self)
        self.root = self.base / '프로젝트'
        self.root.mkdir()
        self.put(self.root / '.git/HEAD', 'ref: refs/heads/main\n')
        self.source = self.put(self.root / 'AGENTS.md', 'Project instructions.\n')
        self.run_count = 0

    def environment(self, name, utf8_mode):
        env = os.environ.copy()
        env.update(LANG=name, LC_ALL=name, LC_CTYPE=name,
                   PYTHONUTF8=str(utf8_mode), PYTHONCOERCECLOCALE='0',
                   PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
        return env

    def metadata(self, env):
        result = subprocess.run([sys.executable, '-B', '-c', METADATA], env=env,
                                capture_output=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def latin1_environment(self):
        try:
            result = subprocess.run(['locale', '-a'], capture_output=True,
                                    encoding='utf-8', errors='replace', timeout=10)
        except FileNotFoundError:
            self.skipTest('Native Latin-1 precondition unavailable: locale inventory tool missing')
        if result.returncode != 0:
            self.skipTest('Native Latin-1 precondition unavailable: locale -a failed')
        installed = result.stdout.splitlines()
        candidates = [name for name in installed
                      if '8859-1' in name.lower() or '88591' in name.lower()
                      or 'latin1' in name.lower() or 'latin-1' in name.lower()]
        observations = []
        for name in candidates:
            env = self.environment(name, 0)
            metadata = self.metadata(env)
            observations.append((name, metadata))
            if (metadata.get('codec') == 'iso8859-1' and metadata.get('utf8_mode') == 0
                    and codecs.lookup(metadata.get('filesystem', 'ascii')).name == 'utf-8'):
                # Guard the native single-byte codec separately from console encoding.
                self.assertEqual(b'\xe9'.decode(metadata['preferred']), '\u00e9')
                self.assertEqual(metadata['utf8_mode'], 0)
                return env
        self.skipTest('No installed native Latin-1 locale with utf8_mode=0 and UTF-8 filesystem; '
                      'observations=' + repr(observations))

    def utf8_environment(self):
        env = self.environment('C', 1)
        metadata = self.metadata(env)
        self.assertEqual(metadata.get('utf8_mode'), 1, metadata)
        self.assertEqual(metadata.get('codec'), 'utf-8', metadata)
        return env

    def scan(self, env, settings=None, resolutions=None):
        self.run_count += 1
        out = self.base / ('run-' + str(self.run_count))
        argv = [sys.executable, '-B', str(SCRIPT), 'scan', '--project', str(self.root),
                '--cwd', str(self.root), '--codex-home', str(self.home), '--out', str(out)]
        for flag, value in (('--settings', settings), ('--resolutions', resolutions)):
            if value is not None:
                path = self.base / (flag[2:] + '.json')
                self.put(path, json.dumps(value, ensure_ascii=False).encode('utf-8'))
                argv.extend([flag, str(path)])
        result = subprocess.run(argv, env=env, capture_output=True, encoding='utf-8', timeout=10)
        self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        audit = json.loads((out / 'audit.json').read_bytes())
        self.assertFalse(audit['partial'])
        routes = [json.loads(line) for line in (out / 'routes.jsonl').read_bytes().splitlines()]
        return audit, routes

    def check_trust_gate(self, env):
        self.put(self.source, 'Project instructions.\n')
        audit, _ = self.scan(env, settings={'schema_version': 1,
                                          'trust': {str(self.root): 'untrusted'}})
        chain = next(row for row in audit['chains'] if row['cwd'] == str(self.root))
        self.assertEqual(chain['settings']['trust'], 'untrusted')
        self.assertEqual(chain['settings']['trust_key'], str(self.root))
        self.assertGreater(chain['project_original_bytes'], 0)
        self.assertEqual(chain['project_included_bytes'], 0)
        self.assertEqual(chain['loader_outcome'], 'omitted_by_gate')

    def check_declared_base(self, env):
        self.put(self.source, 'Read `guide.md` before editing.\n')
        leaf = self.put(self.base / '기준/guide.md', 'Guide instructions.\n')
        self.assertFalse((self.root / 'guide.md').exists())
        _, routes = self.scan(env, settings={'schema_version': 1, 'declared_bases': {
            str(self.source): {'kind': 'absolute', 'path': str(leaf.parent)}}})
        self.assertTrue(any(row['terminal_path'] == str(leaf) and row['terminal_kind'] == 'leaf'
                            for row in routes))

    def check_resolution(self, env):
        text = '지침.md'
        source_text = 'Read `' + text + '` before editing.\n'
        self.put(self.source, source_text)
        leaf = self.put(self.root / text, 'Resolved instructions.\n')
        start = source_text.index(text)
        decision = {'source': str(self.source),
                    'source_sha256': hashlib.sha256(self.source.read_bytes()).hexdigest(),
                    'span': [start, start + len(text)], 'text': text,
                    'classification': 'read_dependency', 'target': text,
                    'base': {'kind': 'document_dir'}}
        audit, routes = self.scan(env, resolutions=[decision])
        self.assertTrue(any(row['source'] == str(self.source) and row['text'] == text
                            and row['classification'] == 'read_dependency'
                            and row['status'] == 'resolved'
                            for row in audit['graph']['occurrences']))
        self.assertTrue(any(row['terminal_path'] == str(leaf) and row['terminal_kind'] == 'leaf'
                            for row in routes))

    def test_latin1_unicode_trust_key_preserves_untrusted_gate(self):
        self.check_trust_gate(self.latin1_environment())

    def test_latin1_unicode_declared_base_resolves_only_explicit_target(self):
        self.check_declared_base(self.latin1_environment())

    def test_latin1_unicode_resolution_binding_and_target_remain_valid(self):
        self.check_resolution(self.latin1_environment())

    def test_utf8_mode_controls_preserve_equivalent_inputs(self):
        env = self.utf8_environment()
        for check in (self.check_trust_gate, self.check_declared_base, self.check_resolution):
            with self.subTest(check=check.__name__):
                check(env)


if __name__ == '__main__':
    unittest.main()
