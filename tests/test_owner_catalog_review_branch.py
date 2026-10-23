"""Execute the workflow's actual persistence step against a local bare Git remote."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/build-owner-yarn-catalog.yml'


def persistence_script():
    source = WORKFLOW.read_text()
    block = source.split('      - name: Preserve refreshed catalog on a review branch (never push main)\n', 1)[1]
    return '\n'.join(line[10:] for line in block.split('        run: |\n', 1)[1].splitlines())


class ReviewBranchPersistence(unittest.TestCase):
    def test_changed_and_unchanged_catalog_never_write_main(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, remote = root / 'repo', root / 'remote.git'
            repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=repo, text=True, stderr=subprocess.PIPE).strip()
            git('init', '-b', 'main')
            git('config', 'user.name', 'Synthetic test')
            git('config', 'user.email', 'test@example.invalid')
            catalog = repo / 'data/yarn-catalog/mz100-catalog-3000.json'
            catalog.parent.mkdir(parents=True)
            catalog.write_text('{"generation":1}\n')
            git('add', '.')
            git('commit', '-m', 'Synthetic baseline')
            baseline = git('rev-parse', 'HEAD')
            subprocess.run(['git', 'clone', '--bare', str(repo), str(remote)], check=True, capture_output=True)
            git('remote', 'add', 'origin', str(remote))
            env = {**os.environ, 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1',
                   'GITHUB_STEP_SUMMARY': str(root / 'summary')}
            script = persistence_script()
            subprocess.run(['bash', '-euo', 'pipefail', '-c', script], cwd=repo, env=env, check=True, capture_output=True)
            self.assertEqual(git('branch', '--show-current'), 'main')
            self.assertEqual(git('ls-remote', 'origin', 'refs/heads/main').split()[0], baseline)
            self.assertNotIn('review/', git('ls-remote', '--heads', 'origin'))
            catalog.write_text('{"generation":2}\n')
            subprocess.run(['bash', '-euo', 'pipefail', '-c', script], cwd=repo, env=env, check=True, capture_output=True)
            proposed = git('rev-parse', 'HEAD')
            self.assertNotEqual(proposed, baseline)
            self.assertEqual(git('ls-remote', 'origin', 'refs/heads/main').split()[0], baseline)
            self.assertEqual(git('ls-remote', 'origin', 'refs/heads/review/owner-yarn-catalog-123-1').split()[0], proposed)
            self.assertEqual(git('show', 'HEAD:data/yarn-catalog/mz100-catalog-3000.json'), '{"generation":2}')


if __name__ == '__main__':
    unittest.main()
