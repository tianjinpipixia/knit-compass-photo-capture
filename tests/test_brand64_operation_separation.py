"""Offline event contracts and real pre-API gates against disposable Git fixtures."""
import fnmatch
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


binding = load('operation_binding', 'scripts/brand64_daily_pipeline_binding.py')
runner = load('operation_runner', 'scripts/run_brand64_gemini_md_free_tier.py')
pages = load('operation_pages', 'scripts/prepare_pages_manual.py')
snapshot_tests = load('operation_snapshot_fixture', 'tests/test_brand64_daily_pipeline_binding.py')


def workflow(name):
    # BaseLoader preserves the Actions key "on" instead of YAML 1.1 boolean conversion.
    return yaml.load((ROOT / '.github/workflows' / name).read_text(), Loader=yaml.BaseLoader)


def triggered(config, event, paths=(), branch='main'):
    rule = config['on'].get(event)
    if event not in config['on']:
        return False
    rule = rule or {}
    return (not rule.get('branches') or branch in rule['branches']) and (
        not rule.get('paths') or any(fnmatch.fnmatch(path, pattern)
                                   for path in paths for pattern in rule['paths']))


class EventSeparationTests(unittest.TestCase):
    def test_code_events_only_select_validation(self):
        collect = workflow('run-brand64-official-direct-scan.yml')
        ai = workflow('run-brand64-gemini-md-free-tier.yml')
        candidate = workflow('prepare-pages-manual.yml')
        ci = workflow('validate-brand64-flash-pipeline.yml')
        self.assertEqual(set(collect['on']), {'schedule', 'workflow_dispatch'})
        self.assertEqual(set(ai['on']), {'workflow_dispatch'})
        self.assertEqual(set(candidate['on']), {'workflow_dispatch'})
        for paths in [('scripts/brand64_canonical_store.py', 'tests/test_brand64_canonical_store.py'),
                      ('.github/workflows/run-brand64-official-direct-scan.yml',),
                      ('.github/workflows/run-brand64-gemini-md-free-tier.yml',),
                      ('tests/test_brand64_operation_separation.py',)]:
            for event in ('push', 'pull_request'):
                with self.subTest(paths=paths, event=event):
                    self.assertTrue(triggered(ci, event, paths))
                    for operational in (collect, ai, candidate):
                        self.assertFalse(triggered(operational, event, paths))
        self.assertFalse(triggered(ai, 'workflow_run'))
        self.assertFalse(triggered(ai, 'push', ('config/gemini-md-free-tier-smoke-trigger-20260907.txt',)))
        self.assertEqual(ci['permissions'], {'contents': 'read'})
        self.assertNotIn('secrets.', json.dumps(ci))

    def test_legitimate_schedules_and_existing_collection_stages_remain(self):
        expected = {'run-brand64-official-direct-scan.yml': '30 20 * * *',
                    'monitor-brand64-daily-freshness.yml': '40 21 * * *',
                    'build-owner-yarn-catalog.yml': '17 21 * * 1'}
        for name, cron in expected.items():
            self.assertEqual(workflow(name)['on']['schedule'], [{'cron': cron}])
            self.assertIn('workflow_dispatch', workflow(name)['on'])
        collect = workflow('run-brand64-official-direct-scan.yml')
        commands = '\n'.join(step.get('run', '') for step in collect['jobs']['direct-scan']['steps'])
        for stage in ('flash', 'retry', 'deep', 'check'):
            self.assertIn('--stage ' + stage, commands)
        self.assertIn('create-publish', commands)
        self.assertIn('PUBLISH_HOLD', commands)
        yarn = workflow('build-owner-yarn-catalog.yml')
        self.assertEqual(yarn['jobs']['refresh']['if'],
                         "github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'")
        self.assertEqual(workflow('monitor-brand64-daily-freshness.yml')['permissions'], {'contents': 'read'})

    def test_manual_input_gate_precedes_step_scoped_model_secret(self):
        job = workflow('run-brand64-gemini-md-free-tier.yml')['jobs']['gemini-md']
        self.assertIn("github.ref == 'refs/heads/main'", job['if'])
        self.assertNotIn('GEMINI_API_KEY', job['env'])
        steps = job['steps']
        gate = next(i for i, s in enumerate(steps) if 'verify-manual' in s.get('run', ''))
        api = next(i for i, s in enumerate(steps) if s.get('id') == 'gemini')
        self.assertLess(gate, api)
        self.assertEqual(steps[api]['env']['GEMINI_API_KEY'], '${{ secrets.GEMINI_API_KEY }}')
        self.assertNotIn('continue-on-error', steps[gate])
        for arg in ('--collection-run-id', '--canonical-commit', '--manifest-sha256'):
            self.assertIn(arg, steps[api]['run'])

    def test_pages_is_read_only_candidate_preparation(self):
        config = workflow('prepare-pages-manual.yml')
        self.assertEqual(config['permissions'], {'contents': 'read'})
        text = json.dumps(config)
        for forbidden in ('deploy-pages', 'configure-pages', 'pages: write', 'id-token', 'secrets.'):
            self.assertNotIn(forbidden, text)
        self.assertIn("github.ref == 'refs/heads/main'", config['jobs']['prepare']['if'])
        self.assertIn('no build or deployment was performed', text)


class ManualGenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'checkout'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Offline fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.direct = self.repo / binding.PREFIX
        snapshot_tests.Brand64DailyPipelineBindingTests().make_direct_snapshot(self.direct)
        binding.build_binding(self.direct, expected_date='2026-09-09', collection_run_id='12345')
        (self.repo / 'index.html').write_text('<title>Offline candidate</title>')
        (self.repo / 'docs').mkdir()
        (self.repo / 'docs/index.html').write_text('<title>Explicit docs candidate</title>')
        (self.repo / 'scripts').mkdir()
        shutil.copy(ROOT / 'scripts/brand64_daily_pipeline_binding.py', self.repo / 'scripts')
        self.git('add', '.')
        self.git('commit', '-m', 'Synthetic snapshot')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        self.git('update-ref', 'refs/remotes/origin/brand64/flash-feed', self.sha)
        self.git('update-ref', 'refs/remotes/origin/main', self.sha)
        self.digest = binding.sha256_file(self.direct / binding.MANIFEST_RELATIVE)
        self.args = dict(repository=self.repo, expected_date='2026-09-09',
                         collection_run_id='12345', canonical_commit=self.sha, manifest_sha256=self.digest)

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, stderr=subprocess.PIPE, text=True)

    def test_exact_commit_remains_usable_after_canonical_tip_advances(self):
        (self.repo / 'new-tip.txt').write_text('A newer generation need not change the requested generation')
        self.git('add', '.')
        self.git('commit', '-m', 'New tip')
        self.git('update-ref', 'refs/remotes/origin/brand64/flash-feed', self.git('rev-parse', 'HEAD').strip())
        result = binding.verify_manual_analysis_input(self.direct, **self.args)
        self.assertEqual(result['collection_run_id'], '12345')
        self.assertEqual(result['publication_status'], 'PUBLISH_HOLD')

    def test_mismatches_reject_before_model_or_network(self):
        cases = [('collection_run_id', '54321'), ('collection_run_id', ''),
                 ('collection_run_id', '1; echo unsafe'), ('canonical_commit', 'HEAD'),
                 ('canonical_commit', '0' * 40), ('manifest_sha256', '0' * 64),
                 ('manifest_sha256', ''), ('expected_date', '2026-09-10')]
        for field, value in cases:
            args = {**self.args, field: value}
            with self.subTest(field=field, value=value), \
                 patch.object(runner, 'ROOT', self.repo), patch.object(runner, 'DIRECT_ROOT', self.direct), \
                 patch.object(runner, 'today_jst', return_value=args['expected_date']), \
                 patch.dict(os.environ, {'GEMINI_API_KEY': 'synthetic-never-used'}), \
                 patch.object(runner.urllib.request, 'urlopen', side_effect=AssertionError('network forbidden')) as network, \
                 patch.object(runner, 'call_gemini') as api, \
                 patch.object(runner.sys, 'argv', ['runner', '--date', args['expected_date'],
                     '--collection-run-id', args['collection_run_id'], '--canonical-commit', args['canonical_commit'],
                     '--manifest-sha256', args['manifest_sha256']]):
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    runner.main()
                network.assert_not_called()
                api.assert_not_called()

    def test_valid_gate_with_missing_key_stops_without_api(self):
        with patch.object(runner, 'ROOT', self.repo), patch.object(runner, 'DIRECT_ROOT', self.direct), \
             patch.object(runner, 'today_jst', return_value='2026-09-09'), \
             patch.dict(os.environ, {'GEMINI_API_KEY': ''}), patch.object(runner, 'call_gemini') as api, \
             patch.object(runner.sys, 'argv', ['runner', '--date', '2026-09-09', '--collection-run-id', '12345',
                 '--canonical-commit', self.sha, '--manifest-sha256', self.digest]):
            self.assertEqual(runner.main(), 2)
            api.assert_not_called()

    def test_actual_restore_shell_uses_pinned_commit_and_leaves_index_clean(self):
        # Only a file://-free local bare repository is used as origin.
        self.git('branch', 'brand64/flash-feed', self.sha)
        remote = Path(self.temp.name) / 'remote.git'
        subprocess.run(['git', 'clone', '--bare', str(self.repo), str(remote)],
                       check=True, capture_output=True)
        self.git('remote', 'add', 'origin', str(remote))
        (self.direct / 'latest.json').write_text('{"unconfirmed":true}\n')
        bin_path = Path(self.temp.name) / 'bin'
        bin_path.mkdir()
        date = bin_path / 'date'
        date.write_text('#!/bin/sh\necho 2026-09-09\n')
        date.chmod(0o755)
        job = workflow('run-brand64-gemini-md-free-tier.yml')['jobs']['gemini-md']
        script = next(s['run'] for s in job['steps'] if 'verify-manual' in s.get('run', ''))
        env = {**os.environ, 'CANONICAL_COMMIT': self.sha, 'MANIFEST_SHA256': self.digest,
               'UPSTREAM_COLLECTION_RUN_ID': '12345', 'PATH': str(bin_path) + os.pathsep + os.environ['PATH']}
        result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                                cwd=self.repo, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'VALID')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        self.assertEqual(self.git('status', '--porcelain'), '')
        for field, invalid in [('CANONICAL_COMMIT', 'HEAD'), ('MANIFEST_SHA256', ''),
                               ('UPSTREAM_COLLECTION_RUN_ID', '12345; exit 0')]:
            with self.subTest(field=field):
                rejected = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                    cwd=self.repo, env={**env, field: invalid}, capture_output=True)
                self.assertNotEqual(rejected.returncode, 0)

    def test_unrelated_commit_and_locally_rebound_input_are_rejected(self):
        unrelated = self.git('commit-tree', self.git('rev-parse', 'HEAD^{tree}').strip(), '-m', 'Unrelated').strip()
        with self.assertRaisesRegex(ValueError, 'NOT_ON_FEED'):
            binding.verify_manual_analysis_input(self.direct, **{**self.args, 'canonical_commit': unrelated})
        # All local checksums remain internally consistent, but differ from the requested commit.
        coverage = self.direct / 'coverage-state.json'
        coverage.write_text('{}\n')
        binding.build_binding(self.direct, expected_date='2026-09-09', collection_run_id='12345')
        with self.assertRaisesRegex(ValueError, 'COMMITTED_INPUT_MISMATCH'):
            binding.verify_manual_analysis_input(self.direct, **self.args)

    def test_tampered_shard_rejected(self):
        (self.direct / 'cumulative-products/BR-00004.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'SHARD_CHECKSUM_MISMATCH'):
            binding.verify_manual_analysis_input(self.direct, **self.args)

    def test_pages_candidate_pins_source_and_never_claims_publication(self):
        status = self.git('status', '--porcelain')
        for path in ('/', '/docs'):
            with self.subTest(path=path):
                output = Path(self.temp.name) / ('root-output' if path == '/' else 'docs-output')
                result = pages.prepare(self.repo, output, self.sha, path)
                self.assertFalse(result['ready_for_deployment'])
                self.assertFalse(result['pages_settings_verified'])
                self.assertEqual(result['code_commit'], self.sha)
                self.assertEqual(result['source_archive_sha256'], hashlib.sha256((output / 'source.tar').read_bytes()).hexdigest())
        self.assertEqual(self.git('status', '--porcelain'), status)
        for sha, path in [('HEAD', '/'), (self.sha, '../'), (self.sha, '/unknown')]:
            with self.subTest(sha=sha, path=path), self.assertRaises(ValueError):
                pages.prepare(self.repo, Path(self.temp.name) / 'bad', sha, path)
        unrelated = self.git('commit-tree', self.git('rev-parse', 'HEAD^{tree}').strip(), '-m', 'Unreviewed').strip()
        with self.assertRaisesRegex(ValueError, 'NOT_ON_MAIN'):
            pages.prepare(self.repo, Path(self.temp.name) / 'bad', unrelated, '/')


if __name__ == '__main__':
    unittest.main()
