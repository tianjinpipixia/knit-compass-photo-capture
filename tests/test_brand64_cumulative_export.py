import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import publish_brand64_flash_feed as publisher
from jun_care_labels import care_from_strip
from official_care_text import CARE_TEXT_SOURCE, care_from_text
import prepare_brand64_owner_review as owner_review


class CumulativeObservedProductExportTests(unittest.TestCase):
    def test_owner_payload_omits_identity_history_only_when_exceeding_the_browser_limit(self):
        row = {'product_code':'33288','product_name':'ニット',
               'legacy_identity_records':[{'product_name':'過去の記録'*250}]}
        shard = {'brand_id':'BR-00018','records':[row]}
        self.assertEqual(json.loads(owner_review.encode_owner_shard(shard)),shard)
        with patch.object(owner_review,'OWNER_SHARD_BYTE_LIMIT',150):
            payload = json.loads(owner_review.encode_owner_shard(shard))
            self.assertEqual(payload['records'],[{'product_code':'33288','product_name':'ニット'}])
        self.assertIn('legacy_identity_records',row)

    def test_doclasse_supplement_preserves_previously_confirmed_care(self):
        url = 'https://www.doclasse.com/item/detail/1_1_33288/090'
        evidence = {'source_url':url,'source_sha256':'b'*64,'retrieved_at_utc':'2026-11-23T02:40:40+00:00'}
        dry_only = {**care_from_text('ドライクリーニング（石油系）'),**evidence}
        row = {'product_url':url,'function_claims':['接触冷感']}
        owner_review.apply_doclasse_review(row,(dry_only,{'UVカット':'95%以上UVカット'},evidence))
        self.assertEqual(row['care_label']['home_wash'],'unknown')
        self.assertEqual(row['care_label']['dry_clean'],'allowed')
        self.assertEqual(row['function_claims'],['接触冷感','UVカット'])
        saved = {**care_from_text('手洗い可'),**evidence}
        row['care_label'] = saved
        owner_review.apply_doclasse_review(row,(dry_only,{},evidence))
        self.assertEqual(row['care_label'],saved)

    def test_world_browser_reviews_attach_to_the_exact_item_and_keep_the_capture_date(self):
        brand = 'BR-00015'
        root_url = 'https://store.world.co.jp/brand/grove/item/'
        date = '2026-11-22'
        codes = ['BR76825F0054', 'BR76826S0125']
        products = [
            {'brand_id': brand, 'brand_name': 'grove', 'product_name': 'ニット',
             'product_url': root_url+code, 'product_code': code,
             'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED'}
            for code in codes
        ]
        products.append({**products[0], 'product_url': root_url+'BR76825F0055'})
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root/'known-products.json').write_text(json.dumps({
                brand+'|'+product['product_url']: product for product in products
            }))

            def export(on):
                (root/'latest.json').write_text(json.dumps({
                    'observed_date': on, 'product_count': len(products), 'product_observed_brand_count': 1,
                }))
                (root/'coverage-state.json').write_text(json.dumps({
                    brand: {'brand_name': 'grove', 'observed_date': on, 'surface_items': products},
                }))
                (root/'feed.json').write_text(json.dumps({'summary': {'observed_date': on}}))
                publisher.build_observed_product_shards(root)
                publisher.build_cumulative_product_shards(root)
                return [
                    {row['product_url']: row.get('care_label') for row in
                     json.loads((root/f'{directory}/{brand}.json').read_text())['records']}
                    for directory in ('observed-products', 'cumulative-products')
                ]

            for rows in export(date):
                self.assertIsNone(rows[products[-1]['product_url']])
                hand, machine = [rows[root_url+code] for code in codes]
                self.assertEqual((hand['home_wash'], hand['max_water_c'], hand['dry_clean'], hand['dry_solvent']),
                                 ('hand', 40, 'allowed', 'F'))
                self.assertEqual((machine['home_wash'], machine['max_water_c'], machine['home_cycle'], machine['dry_clean']),
                                 ('machine', 40, 'very_gentle', 'prohibited'))
                self.assertEqual(machine['source_url'], root_url+codes[1])
                self.assertEqual(machine['evidence_kind'], 'official_browser_image')

            day, cumulative = export('2026-11-23')
            self.assertTrue(all(care is None for care in day.values()))
            self.assertTrue(cumulative[root_url+codes[0]]['retrieved_at_utc'].startswith(date))

    def test_world_browser_review_preserves_the_newer_verified_label(self):
        brand = 'BR-00015'
        code = 'BR76825F0054'
        url = 'https://store.world.co.jp/brand/grove/item/'+code
        sources = json.loads((publisher.COLLECTOR_CONFIG/'brand64-free-direct-sources.json').read_text())['brands']
        reviews = publisher.world_care_reviews(sources)
        item = {'brand_id': brand, 'product_code': code, 'product_url': url}
        newer = {'source_url': url, 'status': 'verified', 'retrieved_at_utc': '2026-11-22T01:59:00Z'}
        item['care_label'] = newer
        publisher.attach_world_review(item, reviews, '2026-11-22', same_day=True)
        self.assertIs(item['care_label'], newer)

    def test_world_browser_review_attaches_material_to_the_matching_product(self):
        brand = 'BR-00015'
        code = 'BR76825F0067'
        url = 'https://store.world.co.jp/brand/grove/item/' + code
        sources = json.loads((publisher.COLLECTOR_CONFIG/'brand64-free-direct-sources.json').read_text())['brands']
        reviews = publisher.world_care_reviews(sources)
        item = {'brand_id': brand, 'product_code': code, 'product_url': url}
        stale = item.copy()
        publisher.attach_world_review(stale, reviews, '2026-11-22', same_day=False)
        self.assertNotIn('material_composition', stale)
        different = {**item, 'product_url': url[:-1]+'8'}
        publisher.attach_world_review(different, reviews, '2026-11-23', same_day=True)
        self.assertNotIn('material_composition', different)
        publisher.attach_world_review(item, reviews, '2026-11-23', same_day=True)
        self.assertEqual(item['material_composition'], 'アクリル87％ ポリエステル13％')
        self.assertEqual(item['composition_detail_evidence']['source_sha256'], item['care_label']['source_sha256'])
        self.assertEqual((item['care_label']['max_water_c'], item['care_label']['dry_clean']), (30, 'prohibited'))
        item['material_composition'] = 'アクリル87% / ポリエステル13%'
        publisher.attach_world_review(item, reviews, '2026-11-23', same_day=True)
        self.assertEqual(item['material_composition'], 'アクリル87% / ポリエステル13%')

    def test_world_browser_review_preserves_the_official_feature_tag_evidence(self):
        conf = publisher.COLLECTOR_CONFIG
        sources = json.loads((conf/'brand64-free-direct-sources.json').read_text())['brands']
        registry = json.loads((conf/'brand64-world-care-reviews.json').read_text())
        item = next(row for row in registry if row['product_code']=='BR63726F0228')
        tags = {'マシンウォッシャブル': 'https://store.world.co.jp/search?ta=DE09'}
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = root/'brand64-world-care-reviews.json'
            path.write_text(json.dumps([{**item,'related_function_tags':tags}]))
            with patch.object(publisher,'COLLECTOR_CONFIG',root):
                reviews = publisher.world_care_reviews(sources)
                row = {key:item[key] for key in ('brand_id','product_code','product_url')}
                row['function_claims'] = ['抗ピリング']
                publisher.attach_world_review(row,reviews,'2026-11-23',same_day=True)
                self.assertEqual(row['function_claims'], ['抗ピリング','洗濯機洗い可'])
                self.assertEqual(row['function_browser_evidence']['tag_urls'], tags)
                self.assertEqual(row['function_browser_evidence']['source_sha256'], item['source_sha256'])
                url = 'https://example.com/search?ta=DE09'
                path.write_text(json.dumps([{**item,'related_function_tags':{'マシンウォッシャブル':url}}]))
                with self.assertRaises(ValueError):
                    publisher.world_care_reviews(sources)

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
            composition = {**detail, 'composition': 'レーヨン 50% ポリエステル 30% ナイロン 20%',
                           'composition_evidence': 'OFFICIAL_MATCHING_PRODUCT_TABLE'}
            saved = exported_function(composition)
            self.assertEqual(saved['material_composition'], composition['composition'])
            self.assertEqual(saved['composition_detail_evidence']['source_sha256'], 'a'*64)
            self.assertEqual(exported_function({**composition, 'retrieved_at_utc': '2026-11-20T14:59:59Z'})
                             ['material_composition'], '')
            self.assertEqual(exported_function({**detail,'function_claims':[]})['care_label']['dry_clean'],
                             'prohibited')
            text_only = {**detail, 'evidence_level': CARE_TEXT_SOURCE, 'function_claims': [],
                         'care_label':care_from_text('手洗い')}
            saved_text = exported_function(text_only)['care_label']
            self.assertEqual((saved_text['source_text'], saved_text['dry_clean']), ('手洗い','unknown'))
            tampered = {**text_only,'care_label':{**text_only['care_label'],'dry_clean':'allowed'}}
            self.assertNotIn('care_label', exported_function(tampered))
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
