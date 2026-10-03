import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('md_status', ROOT / 'scripts/brand64_gemini_md_status.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def record(time, status, date='2026-10-02'):
    return (f'data/brand-md-monitoring/gemini-md/{date}/gemini-md-{time}.json', {
        'format': 'KC_BRAND64_GEMINI_MD_FREE_TIER', 'generated_at_utc': time,
        'observation_date': date, 'gemini_execution_status': status})


class MdStatusTests(unittest.TestCase):
    def test_local_records_normalizes_absolute_and_relative_roots(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = pathlib.Path(directory)
            path, artifact = record('2026-10-02T01:00:00Z', 'SUCCESS')
            target = root / path
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(artifact))
            absolute = root / mod.MD_ROOT
            relative = pathlib.Path(os.path.relpath(absolute, ROOT))
            records = mod.local_records(absolute)
            self.assertEqual(records, mod.local_records(relative))
            self.assertEqual(records[0][0], target.relative_to(ROOT).as_posix())

    def run_restore_step(self, with_artifact=False, with_handoff=False, broken_remote=False):
        workflow = (ROOT / '.github/workflows/run-brand64-gemini-md-free-tier.yml').read_text()
        block = workflow.split('      - name: Restore current MD history and last successful artifact\n', 1)[1]
        script = block.split('run: |\n', 1)[1].split('\n      - name:', 1)[0]
        script = '\n'.join(line[10:] for line in script.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            remote = root / 'remote.git'
            checkout = root / 'checkout'
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
            checkout.mkdir()
            def git(*args):
                return subprocess.run(['git', *args], cwd=checkout, check=True, capture_output=True)
            git('init')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.invalid')
            git('remote', 'add', 'origin', str(root / 'missing.git' if broken_remote else remote))
            (checkout / 'scripts').mkdir()
            shutil.copy(ROOT / 'scripts/brand64_gemini_md_status.py', checkout / 'scripts')
            git('add', '.')
            git('commit', '-m', 'Initial checkout')
            if with_artifact or with_handoff:
                for time, status in [('2026-10-02T01:00:00Z', 'SUCCESS'),
                                     ('2026-10-02T02:00:00Z', 'GEMINI_SCAN_INCOMPLETE')]:
                    path, artifact = record(time, status)
                    target = checkout / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(artifact))
                if with_handoff:
                    git('add', '.')
                    git('commit', '-m', 'MD history')
                    git('push', 'origin', 'HEAD:refs/heads/brand64/gemini-md-test')
                    shutil.rmtree(checkout / mod.MD_ROOT)
            result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                                    cwd=checkout, capture_output=True, text=True)
            if broken_remote:
                self.assertNotEqual(result.returncode, 0)
                return
            self.assertEqual(result.returncode, 0, result.stderr)
            pointer_path = checkout / mod.MD_ROOT / 'latest.json'
            if with_artifact or with_handoff:
                pointer = json.loads(pointer_path.read_text())
                self.assertEqual(pointer['gemini_execution_status'], 'GEMINI_SCAN_INCOMPLETE')
                self.assertEqual(pointer['latest_successful_scan_date'], '2026-10-02')
                for key in ('artifact_path', 'latest_successful_artifact_path'):
                    self.assertFalse(pathlib.Path(pointer[key]).is_absolute())
                    self.assertTrue((checkout / pointer[key]).is_file())
                self.assertEqual(pointer['publication_status'], 'PUBLISH_HOLD')
                self.assertTrue(pointer['human_review_required'])
            else:
                self.assertFalse(pointer_path.exists())

    def test_workflow_no_handoff_restores_checkout_artifacts(self):
        self.run_restore_step(with_artifact=True)

    def test_workflow_first_run_without_history_succeeds(self):
        self.run_restore_step()

    def test_workflow_fetches_existing_handoff(self):
        self.run_restore_step(with_handoff=True)

    def test_workflow_remote_error_is_not_hidden(self):
        self.run_restore_step(broken_remote=True)

    def test_same_day_failure_retains_last_success(self):
        success = record('2026-10-02T01:00:00Z', 'SUCCESS')
        fail = record('2026-10-02T02:00:00Z', 'GEMINI_SCAN_INCOMPLETE')
        prior = record('2026-10-01T01:00:00Z', 'SUCCESS', '2026-10-01')
        pointer = mod.make_pointer([fail, prior, success])
        self.assertEqual(pointer['artifact_path'], fail[0])
        self.assertEqual(pointer['latest_successful_artifact_path'], success[0])
        self.assertEqual(pointer['latest_successful_scan_date'], '2026-10-02')
        self.assertEqual(pointer['gemini_execution_status'], 'GEMINI_SCAN_INCOMPLETE')
        self.assertEqual(pointer['publication_status'], 'PUBLISH_HOLD')
        self.assertTrue(pointer['human_review_required'])

    def test_no_success_is_unavailable(self):
        pointer = mod.make_pointer([record('2026-10-02T02:00:00Z', 'GEMINI_SCAN_INCOMPLETE')])
        self.assertNotIn('latest_successful_artifact_path', pointer)

    def test_missing_current_never_falls_back_to_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            legacy = root / 'gemini-primary-scans'
            legacy.mkdir()
            (legacy / 'latest.json').write_text('{"gemini_execution_status":"SUCCESS"}')
            with patch.object(mod, 'MD_ROOT', root / 'gemini-md'):
                self.assertIn('current status unavailable', mod.summary())

    def test_restore_uses_only_current_md_refs_and_artifacts(self):
        path, artifact = record('2026-10-02T01:00:00Z', 'SUCCESS')
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / 'gemini-md'
            target = root / '2026-10-02/gemini-md-test.json'
            outputs = ['refs/remotes/origin/brand64/gemini-md-test\n',
                       f'100644 blob abc\t{target}\n', json.dumps(artifact)]
            with patch.object(mod, 'MD_ROOT', root), patch.object(mod.subprocess, 'check_output', side_effect=outputs) as git:
                mod.restore()
            pointer = json.loads((root / 'latest.json').read_text())
            self.assertEqual(pointer['latest_successful_artifact_path'], pathlib.Path(os.path.relpath(target, ROOT)).as_posix())
            self.assertIn('refs/remotes/origin/brand64/gemini-md-*', git.call_args_list[0].args[0])
