import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from brand64_canonical_store import read_pool, preserve
from publish_brand64_flash_feed import build_cumulative_product_shards


class CanonicalStoreTests(unittest.TestCase):
    def test_doclasse_canonical_restore_export_and_repeated_restart_coalesce_colours_losslessly(self):
        import hashlib
        from brand64_canonical_store import normalize_identities, seed_working_state
        from run_brand64_free_direct_scan import update_baseline
        bid='BR-00018';base='https://www.doclasse.com/item/detail/1_1_33211'
        records=[{'brand_id':bid,'brand_name':'DoCLASSE','product_name':'ニット',
                  'product_url':base+suffix,'scope_status':'BRAND_AND_KNIT_PATH_MATCHED',
                  'first_seen_date':date,'last_seen_date':date,'material_composition':material,
                  'source_url':'https://www.doclasse.com/item?brand_id=1&category_id=12',
                  'source_sha256':suffix or 'bare','listing_evidence':[{'product_url':base+suffix,
                     'source_url':'https://www.doclasse.com/item?brand_id=1&category_id=12','source_sha256':suffix or 'bare'}]}
                 for suffix,date,material in [('/090','2026-09-03','wool'),('/030','2026-09-02','cotton'),('','2026-09-01','viscose')]]
        old={bid+'|'+r['product_url']:r for r in records}
        # The real legacy store contains both bare goods URLs and colour URLs.
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);(root/'cumulative-products').mkdir()
            shard=root/'cumulative-products/BR-00018.json'
            shard.write_text(json.dumps({'brand_id':bid,'observation_date':'2026-10-16','records':records}))
            (root/'cumulative-products/manifest.json').write_text(json.dumps({
                'format':'KC_BRAND64_CUMULATIVE_PRODUCTS_INDEX','observation_date':'2026-10-16',
                'cumulative_unique_product_count':3,'brands':[{'brand_id':bid,'product_count':3,
                    'path':'cumulative-products/BR-00018.json','sha256':hashlib.sha256(shard.read_bytes()).hexdigest()}]}))
            incoming={**records[0],'product_url':base+'/010','product_code':'33211','last_seen_date':'2026-10-17'}
            working,events=update_baseline([{'brand_id':bid,'brand_name':'DoCLASSE','surface_items':[incoming]}],old,'2026-10-17')
            self.assertFalse(any(e['delta_type']=='FIRST_OBSERVED_CANDIDATE' for e in events))
            for original in records:
                self.assertIn(original,next(iter(working.values()))['legacy_identity_records'])
            (root/'known-products.json').write_text(json.dumps(working))
            (root/'latest.json').write_text(json.dumps({'observed_date':'2026-10-17'}))
            (root/'feed.json').write_text(json.dumps({'summary':{'observed_date':'2026-10-17'}}))
            seeded=seed_working_state(root)
            self.assertEqual(len(seeded),1)  # canonical restore must not resurrect colour duplicates
            build_cumulative_product_shards(root)
            exported=read_pool(root);self.assertEqual(len(exported),1)
            product=next(iter(exported.values()))
            self.assertEqual(product['first_seen_date'],'2026-09-01')
            self.assertEqual(product['last_seen_date'],'2026-10-17')
            self.assertTrue(all(r['product_url'] in product['source_url_aliases'] for r in records))
            for r in records:
                snapshot={k:v for k,v in r.items() if k not in ('legacy_identity_records','source_url_aliases')}
                self.assertIn(snapshot,product['legacy_identity_records'])
            self.assertTrue(all(e in product['listing_evidence'] for r in records for e in r['listing_evidence']))
            # A missing checkpoint must restore the deduplicated canonical pool and all prior facts.
            (root/'known-products.json').write_text('{}')
            build_cumulative_product_shards(root)
            self.assertEqual(read_pool(root),exported)
            self.assertEqual(normalize_identities(exported),exported)

    def test_alias_retention_exception_requires_same_doclasse_brand_and_exact_prior_facts(self):
        from publish_brand64_flash_feed import retained_doclasse_alias
        old={'brand_id':'BR-00018','product_url':'https://www.doclasse.com/item/detail/1_1_33211/090',
             'material_composition':'wool'}
        row={**old,'product_url':old['product_url'].replace('/090','/010'),
             'source_url_aliases':[old['product_url']],'legacy_identity_records':[old]}
        self.assertTrue(retained_doclasse_alias(old,{'new':row}))
        for bad in [{**row,'brand_id':'OTHER'}, {**row,'legacy_identity_records':[]},
                    {**row,'source_url_aliases':[]},
                    {**row,'legacy_identity_records':[{**old,'material_composition':'cotton'}]},
                    {**row,'product_url':row['product_url'].replace('33211','99999')}]:
            self.assertFalse(retained_doclasse_alias(old,{'new':bad}))

    def test_common_goods_identity_is_limited_to_official_doclasse_urls(self):
        from brand64_canonical_store import normalize_identities
        from run_brand64_free_direct_scan import product_identity
        base='https://www.doclasse.com/item/detail/1_1_33211'
        for suffix in ['', '/', '/030', '/090/']:
            self.assertEqual(product_identity({'product_url':base+suffix}),'doclasse:33211')
        for host in ['example.com','www.other.com']:
            urls=[f'https://{host}/p?color=red',f'https://{host}/p?color=blue']
            records={str(i):{'brand_id':'OTHER','product_url':url,'product_name':'other'} for i,url in enumerate(urls)}
            self.assertEqual(len(normalize_identities(records)),2)

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
            (root/'feed.json').write_text(json.dumps({'summary': {'observed_date': '2026-09-08'}, 'candidates': []}))
            (root/'detail-results.json').write_text(json.dumps({key: {
                'product_url': url, 'source_url': url, 'composition': 'Cotton 100%',
                'function_claims': ['machine washable'], 'colors': ['navy'],
                'confirmed_design': {'neck': 'crew'},
                'offers': [{'price': '4,990', 'priceCurrency': 'JPY'},
                           {'price': 19.99, 'priceCurrency': 'USD'}],
                'evidence_level': 'OFFICIAL_PRODUCT_JSONLD', 'publication_status': 'PUBLISH_HOLD',
                'human_review_required': True, 'retrieved_at_utc': '2026-09-08T01:00:00Z'}}))
            build_cumulative_product_shards(root)
            before = read_pool(root)
            self.assertEqual(before[key]['official_detail']['composition'], 'Cotton 100%')
            self.assertEqual(before[key]['function_claims'], ['machine washable'])
            self.assertEqual(before[key]['colors'], ['navy'])
            self.assertEqual(before[key]['confirmed_design']['neck'], 'crew')
            self.assertIsNone(before[key].get('regular_price_jpy'))
            self.assertEqual(before[key]['observed_price_jpy'], 4990)
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
