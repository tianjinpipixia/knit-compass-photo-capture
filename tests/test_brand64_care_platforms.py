import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from jun_care_labels import care_observation
from brand64_canonical_store import attach_details
from brand64_flash_pipeline import needs_watched_care
from official_care_text import add_world_listing_features, dot_care_text, dot_detail, dot_detail_request, pal_care_text, title_features
from run_brand64_free_direct_scan import product_detail, source_error


class CarePlatformTests(unittest.TestCase):
    def test_pal_checks_same_product_table_and_brand(self):
        url = 'https://www.palcloset.jp/display/item/DCZ1062205A0129'
        group = {'@type': 'ProductGroup', 'name': '長袖ニット', 'productGroupID': 'DCZ1062205A0129',
                 'brand': {'name': 'DISCOAT(ディスコート)'}, 'description': '洗濯：手洗い可能'}
        html = (f'<link rel="canonical" href="{url}/"><script type="application/ld+json">{json.dumps([group])}</script>'
                '<table><tr><th>品番</th><td>UNRELATED</td></tr><tr><th>取り扱い</th><td>洗濯不可</td></tr></table>'
                '<table><tr><th>品番</th><td>DCZ1062205A0129</td></tr>'
                '<tr><th>取り扱い</th><td>本体:洗濯機洗い可能</td></tr></table>')
        meta = {'adapter': 'pal', 'brand_name': 'DISCOAT'}
        detail = product_detail(html, url, meta)
        detail.update(source_sha256='a'*64, retrieved_at_utc='2026-11-21T23:00:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['dry_clean']), ('machine', 'unknown'))
        with self.assertRaises(ValueError):
            product_detail(html, url, {**meta, 'brand_name': 'Another brand'})
        conflict = pal_care_text('本体:洗濯機洗い可能 ／ 手洗いのみ')
        self.assertEqual(conflict['home_wash'], 'unknown')
        self.assertEqual(pal_care_text('手洗い可/ドライクリーニング 不可')['dry_clean'], 'unknown')

    def test_dot_reads_only_exact_payload_product(self):
        url = 'https://www.dot-st.com/globalwork/disp/item/1106207'
        meta = {'adapter': 'dot', 'brand_name': 'GLOBAL WORK', 'slug': 'globalwork'}
        script = ('function getItemDetailData(timing){let sendData={'
                  '"itemCd":"1106207","shopDir":"globalwork","shopNo":"0000100002",'
                  '"colorCd":"08","ga_url":"/globalwork/disp/item/1106207/",'
                  '"lm":"20261122070100","eafgrnl":eafgrnl};}')
        request = dot_detail_request(script, url, meta)
        self.assertIsNotNone(request)
        self.assertIsNone(dot_detail_request(script, url.replace('1106207', '1067691'), meta))
        item = {'itemCd': '1106207', 'manShopNo': '0000100002', 'brandNm': 'GLOBAL WORK',
                'itemNm': 'ニット', 'washIcon': '132,200,611',
                'tagFunctionList': [{'tagName': '抗ピリング'}, {'tagName': '帯電防止'}]}
        data = {'result': 'true', 'resultDtl': {'item': [item]}}
        detail = dot_detail(json.dumps(data), url, request, meta)
        detail.update(source_sha256='b'*64, retrieved_at_utc='2026-11-21T23:00:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['max_water_c'], care['dry_clean']), ('machine', 30, 'allowed'))
        self.assertEqual(detail['function_claims'], ['抗ピリング', '帯電防止'])
        item['itemCd'] = '1067691'
        self.assertIsNone(dot_detail(json.dumps(data), url, request, meta))

    def test_world_explicit_title_features_are_distinct_from_care_labels(self):
        self.assertEqual(title_features('ニット〖洗濯機OK／接触冷感／毛玉軽減〗'), {
            '洗濯機洗い可': '洗濯機OK', '接触冷感': '接触冷感', '抗ピリング': '毛玉軽減'})
        self.assertEqual(title_features('ニット【洗える／毛玉に注意】'), {})
        meta = {'adapter': 'world', 'slug': 'grove', 'women_category_entry': True}
        item = {'product_name': 'ニット【毛玉軽減】', 'evidence_level': 'OFFICIAL_LISTING_CARD',
                'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED', 'source_sha256': 'a'*64,
                'product_url': 'https://store.world.co.jp/brand/grove/item/BR76825F0054',
                'source_url': 'https://store.world.co.jp/s/brand/grove/category/WB/WB01/',
                'function_claims': ['接触冷感']}
        wrong = {**item, 'source_url': item['source_url'].replace('/grove/', '/index/')}
        add_world_listing_features(wrong, meta)
        self.assertNotIn('function_listing_evidence', wrong)
        add_world_listing_features(item, meta)
        self.assertEqual(item['function_claims'], ['接触冷感', '抗ピリング'])
        self.assertEqual(item['function_listing_evidence']['claim_text'], {'抗ピリング': '毛玉軽減'})
        self.assertNotIn('care_label', item)

    def test_access_response_records_confirmed_edge_provider(self):
        from urllib.error import HTTPError
        url = 'https://store.world.co.jp/brand/grove/item/BR76825F0054'
        result = source_error(url, HTTPError(url, 403, 'Forbidden', {'Server': 'AkamaiGHost'}, None))
        self.assertEqual((result['http_status'], result['access_provider']), (403, 'AKAMAI'))

    def test_legacy_watch_is_revisited_until_care_is_verified(self):
        task = {'brand_id': 'BR-00004', 'reasons': ['OWNER_WATCH'], 'status': 'COMPLETE'}
        sources = {'BR-00004': {'adapter': 'jun'}}
        self.assertTrue(needs_watched_care(task, {}, sources))
        self.assertFalse(needs_watched_care(task, {'care_label': {'status': 'verified'}}, sources))

    def test_cumulative_care_maintains_identity_across_trailing_slash(self):
        url = 'https://www.dot-st.com/globalwork/disp/item/1046363'
        key = 'BR-00006|' + url
        known = {key: {'product_url': url}}
        care = dot_care_text('洗濯記号 132,611')
        detail = {'product_url': url+'/', 'source_url': url+'/', 'care_label': care, 'publication_status': 'PUBLISH_HOLD',
                  'human_review_required': True, 'evidence_level': 'OFFICIAL_PRODUCT_CARE_TEXT',
                  'retrieved_at_utc': '2026-11-21T23:00:00Z', 'source_sha256': 'a'*64}
        attach_details(known, {key+'/': detail})
        stored = known[key]['care_label']
        self.assertEqual(stored['source_url'], url)
        self.assertEqual(stored['source_fetched_url'], url+'/')
