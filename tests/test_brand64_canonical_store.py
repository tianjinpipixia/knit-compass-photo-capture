import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from brand64_canonical_store import read_pool, preserve
from publish_brand64_flash_feed import build_cumulative_product_shards


class CanonicalStoreTests(unittest.TestCase):
    def test_stale_restart_cannot_drop_products_dates_or_evidence(self):
        old = {'a': {'product_name': 'current', 'first_seen_date': '2026-04-01',
                     'last_seen_date': '2026-09-08', 'retrospective_months': ['2026-04']},
               'b': {'product_name': 'preserved'}}
        result = preserve(old, {'a': {'product_name': 'stale', 'first_seen_date': '2026-06-01',
                                     'last_seen_date': '2026-09-07', 'retrospective_months': ['2026-05']}})
        self.assertEqual(result['a']['product_name'], 'current')
        self.assertEqual(result['a']['first_seen_date'], '2026-04-01')
        self.assertEqual(result['a']['retrospective_months'], ['2026-04', '2026-05'])
        self.assertIn('b', result)

    def test_rebuild_uses_canonical_when_checkpoint_loses_a_product_and_embeds_detail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            url = 'https://example.com/product/a'
            key = 'BR-00001|' + url
            row = {'brand_id': 'BR-00001', 'brand_name': 'A', 'product_name': 'A knit',
                   'product_url': url, 'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED',
                   'first_seen_date': '2026-04-01', 'last_seen_date': '2026-09-08',
                   'retrospective_evidence': [{'period': '2026-04', 'url': url}]}
            (root/'known-products.json').write_text(json.dumps({key: row}))
            (root/'latest.json').write_text(json.dumps({'observed_date': '2026-09-08'}))
            (root/'detail-results.json').write_text(json.dumps({key: {
                'product_url': url, 'source_url': url, 'composition': 'Cotton 100%',
                'function_claims': ['machine washable'], 'colors': ['navy'],
                'confirmed_design': {'neck': 'crew'},
                'offers': [{'price': 4990}],
                'evidence_level': 'OFFICIAL_PRODUCT_JSONLD', 'publication_status': 'PUBLISH_HOLD',
                'human_review_required': True, 'retrieved_at_utc': '2026-09-08T01:00:00Z'}}))
            build_cumulative_product_shards(root)
            before = read_pool(root)
            self.assertEqual(before[key]['official_detail']['composition'], 'Cotton 100%')
            self.assertEqual(before[key]['function_claims'], ['machine washable'])
            self.assertEqual(before[key]['colors'], ['navy'])
            self.assertEqual(before[key]['confirmed_design']['neck'], 'crew')
            self.assertEqual(before[key]['regular_price_jpy'], 4990)
            (root/'known-products.json').write_text('{}')
            (root/'detail-results.json').write_text('{}')
            build_cumulative_product_shards(root)
            self.assertEqual(read_pool(root), before)
            shard = root/'cumulative-products/BR-00001.json'
            shard.write_text(shard.read_text().replace('Cotton', 'Corrupt'))
            with self.assertRaisesRegex(ValueError, 'checksum'):
                read_pool(root)


if __name__ == '__main__':
    unittest.main()

class IdentityAliasTests(unittest.TestCase):
    def test_slash_aliases_preserve_both_records_and_repeated_merge_is_stable(self):
        from brand64_canonical_store import normalize_identities
        a={'brand_id':'BR-00001','product_name':'older','product_url':'https://example.com/p/', 'last_seen_date':'2026-08-01','retrospective_months':['2026-04']}
        b={'brand_id':'BR-00001','product_name':'newer','product_url':'https://example.com/p', 'last_seen_date':'2026-09-08','material_composition':'Cotton 100%'}
        result=normalize_identities({'BR-00001|'+a['product_url']:a,'BR-00001|'+b['product_url']:b})
        self.assertEqual(len(result),1)
        row=next(iter(result.values()))
        self.assertEqual(row['product_name'],'newer')
        self.assertEqual(row['retrospective_months'],['2026-04'])
        self.assertEqual(len(row['legacy_identity_records']),2)
        self.assertEqual(normalize_identities(result),result)
