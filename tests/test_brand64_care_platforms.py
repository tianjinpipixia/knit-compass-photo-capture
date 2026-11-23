import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from jun_care_labels import care_observation
from brand64_canonical_store import attach_details
from brand64_flash_pipeline import needs_watched_care, retry_expanded_detail
from official_care_text import add_world_listing_features, dot_detail, dot_detail_request, jis_care_text, pal_care_text, title_features
from run_brand64_free_direct_scan import product_detail, source_error


class CarePlatformTests(unittest.TestCase):
    def test_onward_keeps_only_care_confirmed_for_every_colour_group(self):
        url = 'https://crosset.onward.co.jp/items/KRWXLW0556'
        product = {'@type': 'Product', 'mpn': 'KRWXLW0556', 'name': '組曲ニット',
                   'brand': {'name': '組曲', 'brandCode': '003'}}
        header = (f'<link rel="canonical" href="{url}">'
                  '<meta property="og:title" content="組曲ニット / 組曲 | ファッション通販">'
                  f'<script type="application/ld+json">{json.dumps(product)}</script>')

        def variant(*codes, composition=''):
            icons = ''.join('<img class="c-item-detail-expand-colors-detail__wash-icon" '
                            f'src="https://crosset.onward.co.jp/images/washIcons/{code}.svg">' for code in codes)
            materials = ('<div class="c-item-detail-expand-colors-detail__info">'
                         '<span class="c-item-detail-expand-colors-detail__info-material">素材</span>'
                         '<div class="c-item-detail-expand-colors-detail__info-detail">'
                         +composition+'</div></div>') if composition else ''
            return '<div class="c-item-detail-expand-colors-detail__body">'+icons+materials+'</div>'

        def doc(*variants):
            return header+'<div class="c-item-description-tab__item-detail-info">'+''.join(variants)+'</div>'

        meta = {'adapter': 'onward-listing', 'brand_name': '組曲', 'brand_code': '003'}
        wash = variant('111','611')
        detail = product_detail(doc(wash, variant('111','210','611','111','611')), url, meta)
        detail.update(source_sha256='a'*64, retrieved_at_utc='2026-11-21T23:00:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['max_water_c'], care['dry_clean'], care['dry_solvent']),
                         ('hand',30,'allowed','F'))
        common = variant('111', '611', composition='綿:100%')
        other = variant('111', '611', composition='毛:100%')
        unrelated = '<table><tr><th>素材</th><td>ナイロン:100%</td></tr></table>'
        matching = product_detail(doc(common, common)+unrelated, url, meta)
        self.assertEqual(matching['composition'], '綿:100%')
        self.assertEqual(matching['composition_evidence'], 'OFFICIAL_MATCHING_PRODUCT_TABLE')
        self.assertNotIn('composition', product_detail(doc(common, other)+unrelated, url, meta))
        self.assertNotIn('composition', product_detail(doc(common, wash)+unrelated, url, meta))
        for wrong in (doc(wash, variant('111','600')), doc(wash, variant()),
                      doc(wash).replace(url, url[:-1]+'7'), doc(wash).replace('003', '702')):
            with self.assertRaises(ValueError):
                product_detail(wrong, url, meta)

    def test_baycrews_uses_care_only_from_the_matching_detail_list(self):
        url = 'https://baycrews.jp/item/detail/slobe/cutsew/26070912306010'
        header = (f'<link rel="canonical" href="{url}">'
                  '<meta property="og:title" content="カーディガン｜SLOBE IENA（スローブ イエナ）の通販｜BAYCREW’S STORE">')
        other = '<dl class="dataDetail"><dt>取扱い</dt><dd>洗濯不可</dd><dt>商品番号</dt><dd id="itemid">25080912215030</dd></dl>'
        detail = ('<dl class="dataDetail"><dt>取扱い</dt><dd>本体:洗濯機洗い（弱）、色あせ</dd>'
                  '<dt>商品番号</dt><dd id="itemid">26070912306010</dd></dl>')
        meta = {'adapter': 'baycrews', 'brand_name': 'SLOBE IENA', 'slug': 'slobe'}
        result = product_detail(header + other + detail, url, meta)
        result.update(source_sha256='a'*64, retrieved_at_utc='2026-11-21T23:00:00Z')
        care = care_observation(result)
        self.assertEqual((care['home_wash'], care['dry_clean']), ('machine', 'unknown'))

    def test_urban_research_uses_the_specification_and_exact_brand_and_code(self):
        url = 'https://www.urban-research.jp/shop/g/gAA26430-2021108/'
        item = {'@type': 'Product', 'name': '『洗濯可』抗ピルキーネックカーディガン',
                'brand': {'name': 'SENSE OF PLACE'}}
        header = f'<link rel="canonical" href="{url}"><script type="application/ld+json">{json.dumps(item)}</script>'
        rows = ('<div class="block-goods-desc_detail"><table><tr><th>品番</th><td>AA26430-2021108</td></tr>'
                '<tr><th>洗濯表記</th><td><span>洗濯機洗い可, ドライクリーニング</span>'
                '<span>商品タグをご覧ください</span></td></tr></table></div>')
        meta = {'brand_name': 'SENSE OF PLACE'}
        result = product_detail(header+rows, url, meta)
        result.update(source_sha256='a'*64, retrieved_at_utc='2026-11-21T23:00:00Z')
        care = care_observation(result)
        self.assertEqual((care['home_wash'], care['dry_clean']), ('machine', 'allowed'))
        self.assertEqual(result['function_claims'], ['抗ピリング'])
        with self.assertRaises(ValueError):
            product_detail(header+rows.replace('AA26430-2021108', 'AA26430-2021105'), url, meta)

    def test_stripe_machine_wash_description_is_a_function_not_a_care_label(self):
        url = 'https://stripe-club.com/brand/american-holic/item/100HA26D0181'
        header = f'<link rel="canonical" href="{url}">'
        item = {'@type': 'Product', 'url': url, 'name': '【接触冷感】ニット',
                'description': '<p>・マシンウォッシャブル：ご家庭の洗濯機でお洗濯して頂けます</p>'}
        doc = header + f'<script type="application/ld+json">{json.dumps(item)}</script>'
        meta = {'adapter': 'stripe', 'brand_name': 'AMERICAN HOLIC', 'slug': 'american-holic'}
        result = product_detail(doc, url, meta)
        self.assertEqual(result['function_claims'], ['接触冷感', '洗濯機洗い可'])
        self.assertNotIn('care_label', result)
        with self.assertRaises(ValueError):
            product_detail(doc, url, {**meta, 'slug': 'earth1999'})

    def test_pal_checks_same_product_table_and_brand(self):
        url = 'https://www.palcloset.jp/display/item/DCZ1062205A0129'
        group = {'@type': 'ProductGroup', 'name': '長袖ニット', 'productGroupID': 'DCZ1062205A0129',
                 'brand': {'name': 'DISCOAT(ディスコート)'}, 'description': '洗濯表記：手洗い可能'}
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
        self.assertEqual(title_features('【辻元舞さん着用】ふんわりVネックニット≪洗濯機OK≫'),
                         {'洗濯機洗い可': '洗濯機OK'})
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

    def test_parser_upgrade_retries_a_detail_error_once(self):
        task = {'status': 'REVIEW_REQUIRED', 'error': 'ValueError: No matching official product detail found'}
        self.assertTrue(retry_expanded_detail(task, {'adapter': 'baycrews'}))
        self.assertTrue(retry_expanded_detail(task, {'brand_name': 'SENSE OF PLACE'}))
        self.assertFalse(retry_expanded_detail({**task, 'detail_parse_version': 2}, {'adapter': 'baycrews'}))
        self.assertFalse(retry_expanded_detail({**task, 'error': 'HTTPError: HTTP Error 403: Forbidden'},
                                               {'adapter': 'baycrews'}))

    def test_cumulative_care_maintains_identity_across_trailing_slash(self):
        url = 'https://www.dot-st.com/globalwork/disp/item/1046363'
        key = 'BR-00006|' + url
        known = {key: {'product_url': url}}
        care = jis_care_text('洗濯記号 132,611', 'dot_symbols')
        detail = {'product_url': url+'/', 'source_url': url+'/', 'care_label': care, 'publication_status': 'PUBLISH_HOLD',
                  'human_review_required': True, 'evidence_level': 'OFFICIAL_PRODUCT_CARE_TEXT',
                  'retrieved_at_utc': '2026-11-21T23:00:00Z', 'source_sha256': 'a'*64}
        attach_details(known, {key+'/': detail})
        stored = known[key]['care_label']
        self.assertEqual(stored['source_url'], url)
        self.assertEqual(stored['source_fetched_url'], url+'/')
