"""R14 group selection rejects lexically identical cwds, preserving symlink aliases."""
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tests'))
import test_discovery as fixtures


class NormalizedGroupSelection(unittest.TestCase):
    # Helper delegation avoids inherited tests; setUp honors CODEX_MD_TEST_TMP.
    setUp = fixtures.DiscoveryTests.setUp
    put = fixtures.DiscoveryTests.put
    cli = fixtures.DiscoveryTests.cli

    def member(self, name):
        path = self.root / name
        self.put(path / 'AGENTS.md', 'Member instructions.\n')
        return path

    def settings(self, selections):
        return {'schema_version': 1, 'environment_groups': [
            {'id': 'group-' + str(index), 'cwds': cwds,
             'effective_loader_settings': {'limit': 32768, 'fallback_names': [],
                                           'root_markers': ['.git'], 'trust': 'trusted'}}
            for index, cwds in enumerate(selections)]}

    def variants(self, cwd):
        return (str(cwd) + '/', str(self.root) + '//a', str(self.root) + '/./a')

    def assert_invalid(self, selections):
        result, _ = self.cli(self.settings(selections))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('Audit input/output error:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_normalized_duplicate_cwds_within_one_group_are_invalid(self):
        cwd = self.member('a')
        for variant in self.variants(cwd):
            with self.subTest(variant=variant):
                self.assertEqual(Path(variant), cwd)
                self.assert_invalid([[str(cwd), variant]])

    def test_normalized_duplicate_cwds_across_groups_are_invalid(self):
        cwd = self.member('a')
        for variant in self.variants(cwd):
            with self.subTest(variant=variant):
                self.assertEqual(Path(variant), cwd)
                self.assert_invalid([[str(cwd)], [variant]])

    def test_distinct_cwds_and_distinct_symlink_aliases_remain_accepted(self):
        first, second = self.member('a'), self.member('b')
        alias = self.root / 'a-alias'
        alias.symlink_to(first, target_is_directory=True)
        self.assertEqual(alias.resolve(), first.resolve())
        for selected in ([str(first), str(second)], [str(first), str(alias)]):
            with self.subTest(selected=selected):
                result, report = self.cli(self.settings([selected]))
                self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
                self.assertFalse(report['partial'])
                members = report['groups'][0]['members']
                self.assertEqual([row['cwd'] for row in members], selected)
                self.assertEqual(len({row['scenario_id'] for row in members}), 2)
                self.assertTrue(all(row['sources'] for row in members))


if __name__ == '__main__':
    unittest.main()
