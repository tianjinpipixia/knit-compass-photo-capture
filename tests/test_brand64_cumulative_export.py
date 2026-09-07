import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import publish_brand64_flash_feed as publisher


class CumulativeObservedProductExportTests(unittest.TestCase):
    def test_cumulative_pool_keeps_prior_days_and_dedupes_by_brand_and_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            known = {
                'BR-A|https://example.com/a': {
                    'brand_id': 'BR-A', 'brand_name': 'A', 'product_name': '商品A',
                    'product_url': 'https://example.com/a', 'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED',
                    'first_seen_date': '2026-09-07', 'last_seen_date': '2026-09-08',
                },
                'BR-A|https://example.com/b': {
                    'brand_id': 'BR-A', 'brand_name': 'A', 'product_name': '商品B',
                    'product_url': 'https://example.com/b', 'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED',
                    'first_seen_date': '2026-09-07', 'last_seen_date': '2026-09-07',
                },
                'BR-B|https://example.com/c': {
                    'brand_id': 'BR-B', 'brand_name': 'B', 'product_name': '商品C',
                    'product_url': 'https://example.com/c', 'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED',
                    'first_seen_date': '2026-09-08', 'last_seen_date': '2026-09-08',
                },
                'BR-B|https://example.com/wait': {
                    'brand_id': 'BR-B', 'brand_name': 'B', 'product_name': '判定待ち',
                    'product_url': 'https://example.com/wait', 'scope_status': 'PRODUCT_SCOPE_REVIEW_REQUIRED',
                    'first_seen_date': '2026-09-08', 'last_seen_date': '2026-09-08',
                },
            }
            (root/'known-products.json').write_text(json.dumps(known))
            (root/'latest.json').write_text(json.dumps({
                'observed_date': '2026-09-08', 'active_brand_count': 64,
                'attempted_brand_count': 64, 'product_observed_brand_count': 2,
                'product_count': 2,
            }))
            generated = publisher.build_cumulative_product_shards(root)
            self.assertIn('cumulative-products/manifest.json', generated)
            manifest = json.loads((root/'cumulative-products/manifest.json').read_text())
            self.assertEqual(manifest['cumulative_unique_product_count'], 3)
            self.assertEqual(manifest['cumulative_product_brand_count'], 2)
            self.assertEqual(manifest['cumulative_from_date'], '2026-09-07')
            self.assertEqual(manifest['observed_product_count_today'], 2)
            self.assertEqual(manifest['dedupe_key'], 'brand_id|product_url')
            self.assertFalse(manifest['formal_product_registration'])
            brand_a = json.loads((root/'cumulative-products/BR-A.json').read_text())
            self.assertEqual(brand_a['product_count'], 2)
            self.assertEqual(brand_a['records'][0]['first_seen_date'], '2026-09-07')
            self.assertNotIn('wait', json.dumps(manifest))


if __name__ == '__main__':
    unittest.main()
