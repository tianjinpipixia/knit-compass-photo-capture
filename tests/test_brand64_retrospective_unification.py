import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import merge_brand64_retrospective_sources as retro


class RetrospectiveUnificationTests(unittest.TestCase):
    def make_repo(self, tmp):
        repo = pathlib.Path(tmp)
        root = repo/'data/brand-md-monitoring/direct-scans'
        root.mkdir(parents=True)
        (repo/'config').mkdir()
        (repo/'config/brand64-active-brands.json').write_text(json.dumps({
            'active_brands': {'BR-1': 'Example Brand'}
        }))
        (repo/'data/brand-md-monitoring/retrospective').mkdir()
        return repo, root

    def test_historical_evidence_enriches_current_record_without_overwriting_current_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, root = self.make_repo(tmp)
            url = 'https://example.com/products/one'
            (root/'known-products.json').write_text(json.dumps({
                'BR-1|'+url: {
                    'brand_id': 'BR-1', 'brand_name': 'Example Brand',
                    'product_name': 'Current Name', 'product_url': url,
                    'display_price': '¥9,999', 'scope_status': retro.COUNTED_SCOPE_STATUS,
                    'first_seen_date': '2026-09-07', 'last_seen_date': '2026-09-08',
                    'sales_start_date': None,
                }
            }))
            (repo/'data/brand-md-monitoring/retrospective/manual-products.json').write_text(json.dumps({
                'source_snapshot_date': '2026-07-21',
                'records': [{
                    'brand_id': 'BR-1', 'brand_name': 'Example Brand',
                    'product_name': 'Historical Name', 'product_code': 'ONE',
                    'product_url': url, 'observed_price_jpy': 4999,
                    'material_composition': '綿100%', 'function_claims': ['UV'],
                    'snapshot_date': '2026-07-21', 'retrospective_months': ['2026-07'],
                    'eligible_for_cumulative': True,
                }]
            }))
            summary = retro.merge_retrospective_sources(root, repo)
            merged = json.loads((root/'known-products.json').read_text())['BR-1|'+url]
            self.assertEqual(merged['display_price'], '¥9,999')
            self.assertEqual(merged['first_seen_date'], '2026-09-07')
            self.assertEqual(merged['last_seen_date'], '2026-09-08')
            self.assertEqual(merged['sales_start_date'], None)
            self.assertEqual(merged['material_composition'], '綿100%')
            self.assertEqual(merged['retrospective_months'], ['2026-07'])
            self.assertEqual(summary['created_cumulative_product_count'], 0)
            self.assertEqual(summary['enriched_existing_product_count'], 1)

    def test_historical_only_product_enters_same_known_product_pool_and_keeps_launch_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, root = self.make_repo(tmp)
            (root/'known-products.json').write_text('{}')
            url = 'https://example.com/products/two'
            (repo/'data/brand-md-monitoring/retrospective/manual-products.json').write_text(json.dumps({
                'source_snapshot_date': '2026-07-21',
                'records': [{
                    'brand_id': 'BR-1', 'brand_name': 'Example Brand',
                    'product_name': 'July Knit', 'product_code': 'TWO',
                    'product_url': url, 'regular_price_jpy': 7000,
                    'observed_price_jpy': 5000, 'material_composition': 'レーヨン80%／ポリエステル20%',
                    'function_claims': ['接触冷感', 'UVカット'],
                    'snapshot_date': '2026-07-21', 'retrospective_months': ['2026-07'],
                    'eligible_for_cumulative': True,
                }, {
                    'brand_id': 'BR-1', 'brand_name': 'Example Brand',
                    'product_name': 'Scope Review', 'product_url': 'https://example.com/products/review',
                    'snapshot_date': '2026-07-21', 'eligible_for_cumulative': False,
                }]
            }))
            summary = retro.merge_retrospective_sources(root, repo)
            known = json.loads((root/'known-products.json').read_text())
            row = known['BR-1|'+url]
            self.assertEqual(row['first_seen_date'], '2026-07-21')
            self.assertEqual(row['sales_start_date'], None)
            self.assertTrue(row['retrospective_only'])
            self.assertEqual(row['scope_status'], retro.COUNTED_SCOPE_STATUS)
            self.assertEqual(summary['created_cumulative_product_count'], 1)
            self.assertEqual(summary['scope_review_only_count'], 1)
            self.assertEqual(len(known), 1)

    def test_august_official_baseline_is_imported_but_inactive_brand_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, root = self.make_repo(tmp)
            (root/'known-products.json').write_text('{}')
            path = repo/'data/brand-md-monitoring/2026-08-16-product-baseline-snapshots.jsonl'
            rows = [
                {'brand_id':'BR-1','brand':'Example Brand','product_name':'August Knit','product_code':'AUG',
                 'official_product_url':'https://example.com/products/aug','observed_date':'2026-08-16',
                 'source_status':'ONLINE_OFFICIAL_PRODUCT_PAGE'},
                {'brand_id':'BR-X','brand':'Inactive','product_name':'Inactive Knit','product_code':'X',
                 'official_product_url':'https://example.com/products/x','observed_date':'2026-08-16',
                 'source_status':'ONLINE_OFFICIAL_PRODUCT_PAGE'},
            ]
            path.write_text('\n'.join(json.dumps(row) for row in rows)+'\n')
            summary = retro.merge_retrospective_sources(root, repo)
            known = json.loads((root/'known-products.json').read_text())
            self.assertIn('BR-1|https://example.com/products/aug', known)
            self.assertNotIn('BR-X|https://example.com/products/x', known)
            self.assertEqual(known['BR-1|https://example.com/products/aug']['retrospective_months'], ['2026-08'])
            self.assertEqual(summary['skipped_inactive_brand_count'], 1)


if __name__ == '__main__':
    unittest.main()
