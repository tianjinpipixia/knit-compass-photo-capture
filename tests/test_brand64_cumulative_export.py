import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import publish_brand64_flash_feed as publisher
from jun_care_labels import care_from_strip


class CumulativeObservedProductExportTests(unittest.TestCase):
    def test_daily_functions_use_exact_product_and_same_japan_date(self):
        url = 'https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM56370'
        date = '2026-11-21'
        listing = {'product_url': url, 'product_code': 'GDM56370',
                   'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED'}
        detail = {'product_url': url, 'source_url': url, 'function_claims': ['手洗い可'],
                  'source_sha256': 'a'*64, 'retrieved_at_utc': '2026-11-20T15:00:00Z',
                  'publication_status': 'PUBLISH_HOLD', 'human_review_required': True,
                  'evidence_level': 'OFFICIAL_PRODUCT_JSONLD',
                  'care_label': care_from_strip('/common/img/sentaku/SE-151.gif',
                                              lambda url:'543efe09e8128d530f27bbdc0e649005d0998926d8205d3cdc63f70a216f1806')}
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root/'latest.json').write_text(json.dumps({'observed_date': date, 'product_count': 1,
                                                      'product_observed_brand_count': 1}))
            (root/'coverage-state.json').write_text(json.dumps({
                'BR-00004': {'observed_date': date, 'surface_items': [listing]}}))

            def exported_function(saved_detail):
                (root/'detail-results.json').write_text(json.dumps({'BR-00004|'+url: saved_detail}))
                publisher.build_observed_product_shards(root)
                return json.loads((root/'observed-products/BR-00004.json').read_text())['records'][0]

            valid = exported_function(detail)
            self.assertEqual(valid['function_claims'], ['手洗い可'])
            self.assertEqual(valid['function_detail_evidence']['source_sha256'], 'a'*64)
            self.assertEqual(valid['material_composition'], '')
            self.assertEqual(valid['care_label']['home_wash'], 'hand')
            self.assertEqual(exported_function({**detail,'function_claims':[]})['care_label']['dry_clean'],
                             'prohibited')
            for invalid in ({'retrieved_at_utc': '2026-11-20T14:59:59Z'},
                            {'retrieved_at_utc': '2026-11-21T09:00:00'},
                            {'source_url': url+'0'}, {'source_sha256': 'x'*64}):
                with self.subTest(invalid=invalid):
                    record = exported_function({**detail, **invalid})
                    self.assertEqual(record['function_claims'], [])
                    self.assertNotIn('function_detail_evidence', record)
                    self.assertNotIn('care_label', record)

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
                'BR-A|https://example.com/regular-line': {
                    'brand_id': 'BR-A', 'brand_name': 'A', 'product_name': '通常ライン確認済み',
                    'product_url': 'https://example.com/regular-line',
                    'scope_status': 'OFFICIAL_REGULAR_LINE_WOMENS_KNIT_CONFIRMED',
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
            (root/'feed.json').write_text(json.dumps({'summary': {'observed_date': '2026-09-08'}, 'candidates': []}))
            generated = publisher.build_cumulative_product_shards(root)
            self.assertIn('cumulative-products/manifest.json', generated)
            manifest = json.loads((root/'cumulative-products/manifest.json').read_text())
            self.assertEqual(manifest['cumulative_unique_product_count'], 4)
            self.assertEqual(manifest['cumulative_product_brand_count'], 2)
            self.assertEqual(manifest['cumulative_from_date'], '2026-09-07')
            self.assertEqual(manifest['observed_product_count_today'], 2)
            self.assertEqual(manifest['dedupe_key'], 'brand_id|product_url')
            self.assertFalse(manifest['formal_product_registration'])
            brand_a = json.loads((root/'cumulative-products/BR-A.json').read_text())
            self.assertEqual(brand_a['product_count'], 3)
            self.assertEqual(brand_a['records'][0]['first_seen_date'], '2026-09-07')
            self.assertIn('regular-line', json.dumps(brand_a))
            self.assertNotIn('wait', json.dumps(manifest))


if __name__ == '__main__':
    unittest.main()
