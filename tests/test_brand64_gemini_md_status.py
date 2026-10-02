import importlib.util
import json
import pathlib
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
            self.assertEqual(pointer['latest_successful_artifact_path'], str(target))
            self.assertIn('refs/remotes/origin/brand64/gemini-md-*', git.call_args_list[0].args[0])
