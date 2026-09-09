import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'pipeline_binding', ROOT / 'scripts/brand64_daily_pipeline_binding.py'
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Brand64DailyPipelineBindingTests(unittest.TestCase):
    def write_json(self, path, value, compact=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(value, ensure_ascii=False, separators=(',', ':') if compact else None) + '\n'
        path.write_text(text, encoding='utf-8')

    def make_direct_snapshot(self, root):
        latest = {
            'format': 'KC_BRAND64_FREE_DIRECT_SCAN',
            'schema_version': '2.0',
            'collector': 'CHATGPT_OFFICIAL_DIRECT',
            'collection_method': 'DIRECT_HTTP_NO_AI_API',
            'observed_date': '2026-09-09',
            'product_count': 1,
            'product_observed_brand_count': 1,
            'attempted_brand_count': 64,
            'scan_status': 'PARTIAL_COVERAGE',
        }
        feed = {'summary': {'observed_date': '2026-09-09'}}
        coverage = {'BR-00004': {'observed_date': '2026-09-09', 'surface_items': []}}
        self.write_json(root / 'latest.json', latest)
        self.write_json(root / 'feed.json', feed)
        self.write_json(root / 'coverage-state.json', coverage)

        shard = {
            'format': 'KC_BRAND64_CUMULATIVE_PRODUCTS_BRAND',
            'schema_version': '1.1',
            'observation_date': '2026-09-09',
            'brand_id': 'BR-00004',
            'brand_name': 'ROPÉ PICNIC',
            'product_count': 1,
            'records': [{'brand_id': 'BR-00004', 'product_name': 'Test knit', 'product_url': 'https://example.test/item'}],
        }
        shard_path = root / 'cumulative-products/BR-00004.json'
        self.write_json(shard_path, shard, compact=True)
        manifest = {
            'format': 'KC_BRAND64_CUMULATIVE_PRODUCTS_INDEX',
            'schema_version': '1.3',
            'observation_date': '2026-09-09',
            'cumulative_unique_product_count': 1,
            'observed_product_count_today': 1,
            'product_observed_brand_count_today': 1,
            'brands': [{
                'brand_id': 'BR-00004',
                'brand_name': 'ROPÉ PICNIC',
                'product_count': 1,
                'path': 'cumulative-products/BR-00004.json',
                'sha256': mod.sha256_file(shard_path),
            }],
            'daily_sources': {
                'latest': {'path': 'latest.json', 'sha256': mod.sha256_file(root / 'latest.json')},
                'feed': {'path': 'feed.json', 'sha256': mod.sha256_file(root / 'feed.json')},
            },
        }
        self.write_json(root / 'cumulative-products/manifest.json', manifest, compact=True)
        return latest

    def test_binding_keeps_collection_run_and_canonical_generation_together(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.make_direct_snapshot(root)
            binding = mod.build_binding(
                root,
                expected_date='2026-09-09',
                collection_run_id='12345',
                collection_run_attempt='2',
                collector_source_sha='abc123',
            )
            verified = mod.verify_binding(
                root,
                expected_date='2026-09-09',
                expected_collection_run_id='12345',
            )
            self.assertEqual(verified['canonical_manifest_sha256'], binding['canonical_manifest_sha256'])
            self.assertEqual(verified['canonical_unique_product_count'], 1)
            self.assertEqual(verified['collector'], 'CHATGPT_OFFICIAL_DIRECT')
            self.assertTrue(verified['analysis_ready'])

    def test_binding_rejects_stale_or_mutated_daily_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.make_direct_snapshot(root)
            mod.build_binding(root, expected_date='2026-09-09', collection_run_id='12345')
            latest = json.loads((root / 'latest.json').read_text(encoding='utf-8'))
            latest['product_count'] = 2
            self.write_json(root / 'latest.json', latest)
            with self.assertRaisesRegex(ValueError, 'CHECKSUM_MISMATCH'):
                mod.verify_binding(root, expected_date='2026-09-09', expected_collection_run_id='12345')

    def test_gemini_artifact_is_stamped_with_exact_collection_snapshot(self):
        with tempfile.TemporaryDirectory() as direct_directory, tempfile.TemporaryDirectory() as gemini_directory:
            direct_root = pathlib.Path(direct_directory)
            gemini_root = pathlib.Path(gemini_directory)
            self.make_direct_snapshot(direct_root)
            binding = mod.build_binding(
                direct_root,
                expected_date='2026-09-09',
                collection_run_id='12345',
                collection_run_attempt='1',
            )
            artifact_path = gemini_root / '2026-09-09/gemini-md-test.json'
            self.write_json(artifact_path, {
                'format': 'KC_BRAND64_GEMINI_MD_FREE_TIER',
                'observation_date': '2026-09-09',
                'gemini_execution_status': 'SUCCESS',
            })
            self.write_json(gemini_root / 'latest.json', {
                'latest_attempted_scan_date': '2026-09-09',
                'artifact_path': str(artifact_path),
                'gemini_execution_status': 'SUCCESS',
            })
            latest = mod.stamp_gemini(
                gemini_root,
                direct_root,
                analysis_run_id='67890',
                analysis_run_attempt='1',
                expected_collection_run_id='12345',
            )
            stamped = json.loads(artifact_path.read_text(encoding='utf-8'))
            self.assertEqual(stamped['analyzer'], 'GEMINI_PRIMARY')
            self.assertEqual(stamped['analysis_input_snapshot']['collection_run_id'], '12345')
            self.assertEqual(stamped['analysis_input_snapshot']['canonical_manifest_sha256'], binding['canonical_manifest_sha256'])
            self.assertEqual(latest['source_collector'], 'CHATGPT_OFFICIAL_DIRECT')
            self.assertEqual(latest['analysis_input_manifest_sha256'], binding['canonical_manifest_sha256'])


if __name__ == '__main__':
    unittest.main()
