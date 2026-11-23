import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from jun_care_labels import care_observation
from brand64_canonical_store import attach_details
from brand64_flash_pipeline import needs_watched_care, retry_expanded_detail
from official_care_text import (
    USAGI_ICONS, add_world_listing_features, dot_detail, dot_detail_request, jis_care_text, pal_care_text,
    title_features, usagi_icon_url,
)
from prepare_brand64_owner_review import reviewed_detail_key
from run_brand64_free_direct_scan import product_detail, source_error


class CarePlatformTests(unittest.TestCase):
    def test_fr_uses_official_washing_field_and_keeps_dry_unknown(self):
        url = 'https://www.gu-global.com/jp/ja/products/E357431-000/00'
        sku = 'E357431-000'
        machine = 'ご家庭の洗濯機でそのまま洗えるマシンウォッシャブル機能付きです。'
        pilling = '毛玉になりにくいアンチピリング素材を使用しています。'
        product = {'productId': sku, 'name': 'ニット', 'washingInformation': '洗濯機',
                   'longDescription': f'【機能と素材について】<br>- {machine}<br>- {pilling}<br>【注意】'}
        payload = {'entity': {'pdpEntity': {sku+'-00': {'product': product}}}}
        html = (f'<link rel="canonical" href="{url}">'
                f'<script>window.__PRELOADED_STATE__ = {json.dumps(payload)}</script>'
                '<section id="productMaterialDescription-content"><p>洗濯機</p></section>')
        brand = {'adapter': 'fr', 'brand_name': 'GU'}
        detail = product_detail(html, url, brand)
        detail.update(source_sha256='a'*64, retrieved_at_utc='2026-11-23T10:00:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['dry_clean']), ('machine', 'unknown'))
        self.assertEqual(detail['function_source_text'], {'洗濯機洗い可': machine, '抗ピリング': pilling})
        forged = {**detail, 'source_url': url.replace('www.gu-global.com', 'example.invalid')}
        self.assertIsNone(care_observation(forged))
        row = {'brand_id': 'BR-00002', 'product_url': url, 'product_code': ''}
        self.assertEqual(reviewed_detail_key(row, brand), ('BR-00002', sku, url))
        self.assertEqual(reviewed_detail_key(row, {'adapter': 'pal'})[1], '')
        self.assertEqual(reviewed_detail_key({**row, 'product_code': 'PRESERVED'}, brand)[1], 'PRESERVED')

    def test_usagi_binds_washing_symbols_to_exact_product_and_all_colours(self):
        url = 'https://usagi-online.com/brand/snidel/item/SND0126F0036'
        brand = {'adapter': 'usagi', 'slug': 'snidel', 'brand_name': 'SNIDEL'}
        assets = {usagi_icon_url(name): entry[1] for name, entry in USAGI_ICONS.items()}

        def group(color, *names):
            icons = ''.join(f'<img src="{usagi_icon_url(name).removeprefix("https://usagi-online.com")}">'
                            for name in names)
            return f'<div class="washing-sku-group" data-sku-color="{color}"><div class="washing-icons">{icons}</div></div>'

        common = (f'<link rel="canonical" href="{url}"><title>ニット｜SNIDEL（スナイデル）</title><h1>ニット</h1>'
                  '<section class="info-washing">')
        same = common + group('OWHT', 'ua', 'e', 'i') + group('BLK', 'ua', 'e', 'i') + '</section>'
        detail = product_detail(same, url, brand, read_care_image_sha=assets.__getitem__)
        detail.update(source_sha256='a'*64, retrieved_at_utc='2026-11-23T10:00:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['max_water_c'], care['dry_clean'], care['dry_solvent']),
                         ('hand', 40, 'allowed', 'F'))
        different = common + group('OWHT', 'ua', 'e', 'i') + group('BRW', 'ub', 'e', 'f') + '</section>'
        care = product_detail(different, url, brand, read_care_image_sha=assets.__getitem__)['care_label']
        self.assertEqual((care['home_wash'], care['dry_clean']), ('unknown', 'allowed'))
        delicate = common + group('NVY', 'ue', 'uw', 'c', 'i') + '</section>'
        care = product_detail(delicate, url, brand, read_care_image_sha=assets.__getitem__)['care_label']
        self.assertEqual((care['home_wash'], care['max_water_c'], care['home_cycle'],
                          care['dry_clean'], care['dry_solvent'], care['dry_cycle']),
                         ('machine', 30, 'very_gentle', 'allowed', 'P', 'gentle'))
        with self.assertRaises(ValueError):
            product_detail(same, url.replace('0036', '0035'), brand, read_care_image_sha=assets.__getitem__)
        with self.assertRaises(ValueError):
            product_detail(same, url, brand, read_care_image_sha=lambda _: '0'*64)

    def test_mix_care_binds_code_to_brand_product_and_official_data_version(self):
        path = '/products/0176270040'
        url = 'https://mix.tokyo'+path
        map_url = 'https://cdn.example.invalid/official-map.json?v=1'
        group = {'@type':'ProductGroup', '@id':path+'#product', 'category':'knit_sweater',
                 'name':'ニット','brand':{'name':'NATURAL BEAUTY BASIC'}}
        fields = f'''<div class="c_detail__item"><h3 class="c_detail__title">商品番号</h3>
          <div class="c_detail__content">0176270040 グレー (020)</div></div>
          <div class="c_detail__item"><h3 class="c_detail__title">洗濯表示</h3>
          <div class="c_detail__content"><div id="wash_images">2141I</div>
          <script>fetch('{map_url}')</script></div></div>'''
        html = (f'<link rel="canonical" href="{url}">'
                f'<script type="application/ld+json">{json.dumps(group)}</script>'+fields)
        meta = {'brand_name':'NATURAL BEAUTY BASIC','adapter':'shopify'}
        mapping = {'codes':{'2141I':['111','600']},'sha256':'b'*64,'url':map_url}
        with patch('official_care_text.mix_symbol_map',return_value=mapping):
            detail = product_detail(html,url,meta)
            detail.update(source_sha256='a'*64,retrieved_at_utc='2026-11-23T03:07:11+00:00')
            care = care_observation(detail)
            self.assertEqual((care['home_wash'], care['max_water_c'], care['dry_clean']),
                             ('hand', 30, 'prohibited'))
            self.assertEqual(care['symbol_map_sha256'],'b'*64)
            for wrong in (html.replace('0040 グレー','0041 グレー'),
                          html.replace('v=1','v=2'), html.replace('NATURAL BEAUTY BASIC','Other')):
                with self.assertRaises(ValueError):
                    product_detail(wrong,url,meta)
            for category, name in (('jacket', '接結ニットジャケット'),
                                   ('knit_onepiece', 'ダブルフェイスニットセットアップ'),
                                   ('other_onepiece', 'スパンコールラメニットセットアップ')):
                def page(name):
                    data = {**group, 'category': category, 'name': name}
                    return html.replace(json.dumps(group), json.dumps(data))

                with self.subTest(category=category):
                    self.assertEqual(product_detail(page(name), url, meta)['care_label']['wash_code'], '2141I')
                    with self.assertRaises(ValueError):
                        product_detail(page('ジャカード'), url, meta)

    def test_united_arrows_reads_only_the_exact_products_care_section(self):
        url = 'https://store.united-arrows.co.jp/brand/glr/item/3500026F0275'
        color_url = url+'?areaid=ebGL000&clr_id=101'
        brand = {'adapter': 'unitedarrows', 'slug': 'glr', 'brand_name': 'green label relaxing'}
        group = {'@type': 'ProductGroup', 'url': url, 'name': 'Vネック ニット',
                 'brand': {'name': 'green label relaxing'}}
        html = (f'<link rel="canonical" href="{url}">'
                f'<script type="application/ld+json">{json.dumps(group)}</script>'
                '<span>商品番号 3518-1-000037</span>'
                '<div class="text-sm leading-normal"><p>商品説明</p>'
                '============================<br>機能性：接触冷感・UVカット<br>'
                'ケア方法：手洗い可<br>============================<br>ドライクリーニング不可</div>')
        detail = product_detail(html, color_url, brand)
        detail.update(source_sha256='a'*64, retrieved_at_utc='2026-11-23T21:13:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['dry_clean']), ('hand', 'unknown'))
        self.assertEqual(detail['function_source_text'], {'接触冷感': '接触冷感', 'UVカット': 'UVカット'})
        different = html.replace('ケア方法：手洗い可', 'ケア方法：洗濯機洗い可・ドライクリーニング可')
        label = product_detail(different, url, brand)['care_label']
        self.assertEqual((label['home_wash'], label['dry_clean']), ('machine', 'allowed'))
        self.assertIsNone(care_observation({**detail, 'source_url': url.replace('store.united-arrows.co.jp', 'example.com')}))
        self.assertNotIn('care_label', product_detail(html.replace('手洗い可', '手洗い可否は表示を確認'), url, brand))
        for bad_html, bad_url in (
            (html, url+'?product=unrelated'),
            (html.replace('green label relaxing', 'Other'), url),
            (html.replace('3518-1-000037', 'missing'), url),
            (html, url.replace('F0275', 'F0276')),
        ):
            with self.assertRaises(ValueError):
                product_detail(bad_html, bad_url, brand)

    def test_ikka_does_not_equate_wet_and_dry_cleaning(self):
        url = 'https://tokyodesignchannel.com/c/ikka/ikkaladies/ikkalknit/12110102'
        canonical = 'https://tokyodesignchannel.com/c/ikka/12110102'
        html = (f'<link rel="canonical" href="{canonical}">'
                '<meta property="og:title" content="ニット,ikka| TOKYO DESIGN CHANNEL">'
                '<dl><dt>商品コード</dt><dd>12110102</dd></dl>'
                '<dl><dt>クリーニング方法</dt><dd>洗濯機洗い可（弱く） ウェットクリーニング（W）</dd></dl>'
                '<dl><dt>素材</dt><dd>綿50% ポリエステル50%</dd></dl>')
        meta = {'brand_name':'ikka','adapter':'ikka'}
        detail = product_detail(html,url,meta)
        detail.update(source_sha256='a'*64,retrieved_at_utc='2026-11-23T03:07:11+00:00')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'],care['dry_clean']),('machine','unknown'))
        self.assertEqual(detail['composition'],'綿50% ポリエステル50%')
        with self.assertRaises(ValueError):
            product_detail(html.replace('<dd>12110102','<dd>12110103'),url,meta)

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

    def test_stripe_reads_independent_function_declarations(self):
        url = 'https://stripe-club.com/brand/american-holic/item/100HA26G0063'
        product = {'@type': 'Product', 'url': url, 'name': 'ニット',
                   'description': '・静電気防止（バイパチニット）<br>・毛玉防止<br>帯電防止加工ではありません。'}
        doc = (f'<link rel="canonical" href="{url}">'
               f'<script type="application/ld+json">{json.dumps(product)}</script>')
        detail = product_detail(doc, url, {'adapter':'stripe','brand_name':'AMERICAN HOLIC','slug':'american-holic'})
        self.assertEqual(detail['function_source_text'], {'帯電防止':'静電気防止（バイパチニット）','抗ピリング':'毛玉防止'})
        self.assertNotIn('care_label', detail)

    def test_stripe_reads_explicit_machine_washing_from_released_product_features(self):
        url = 'https://stripe-club.com/brand/american-holic/item/100HA25G0120'
        meta = {'adapter': 'stripe', 'brand_name': 'AMERICAN HOLIC', 'slug': 'american-holic'}
        feature = ('■機能<br>・ウォッシャブルニット<br>ご家庭の洗濯機でお洗濯して頂けるニットです。'
                   '洗濯ネットをご使用頂き、形を整えて陰平干しして頂くのがおすすめです。')

        def read(description, name='ニット'):
            product = {'@type': 'Product', 'url': url, 'name': name, 'description': description}
            html = (f'<link rel="canonical" href="{url}">'
                    f'<script type="application/ld+json">{json.dumps(product)}</script>')
            detail = product_detail(html, url, meta)
            detail.update(source_sha256='a'*64, retrieved_at_utc='2026-11-23T10:00:00Z')
            return detail

        detail = read(feature)
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['dry_clean']), ('machine', 'unknown'))
        self.assertNotIn('max_water_c', care)
        self.assertEqual(detail['function_claims'], ['洗濯機洗い可'])
        for description, name in (
            (feature, '【予約】ニット'),
            (feature+'<br>※家庭洗濯不可', 'ニット'),
            (feature.replace('■機能', '■関連商品'), 'ニット'),
        ):
            with self.subTest(description=description, name=name):
                labelled_description = description + '<br>・静電気防止（バイパチニット）'
                self.assertNotIn('care_label', read(labelled_description, name))

    def test_stripe_reads_explicit_washing_instructions_for_the_exact_product(self):
        url = 'https://stripe-club.com/brand/american-holic/item/100HA25G0124'
        instructions = ('【お洗濯について】<br>・液温は40℃を限度とし、手洗いが可能です。<br>'
                        '・ドライクリーニングは可能です。（溶剤は石油系を使用してください）')
        item = {'@type':'Product','url':url,'name':'ニット','description':instructions}
        doc = (f'<link rel="canonical" href="{url}">'
               f'<script type="application/ld+json">{json.dumps(item)}</script>')
        meta = {'adapter':'stripe','brand_name':'AMERICAN HOLIC','slug':'american-holic'}
        detail = product_detail(doc,url,meta)
        detail.update(source_sha256='a'*64,retrieved_at_utc='2026-11-23T03:07:11+00:00')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'],care['max_water_c'],care['dry_clean'],care['dry_solvent']),
                         ('hand',40,'allowed','F'))

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

    def test_pal_reads_independent_product_care_bullets(self):
        url = 'https://www.palcloset.jp/display/item/DCE2062205A0002'
        group = {'@type': 'ProductGroup', 'name': '長袖ニット', 'productGroupID': 'DCE2062205A0002',
                 'brand': {'name': 'DISCOAT'},
                 'description': '・手洗い可能：40℃限度<br>・ドライクリーニング：可能<br>'
                                '・通常はドライクリーニング不可の場合もあります。'}
        meta = {'adapter': 'pal', 'brand_name': 'DISCOAT'}

        def read():
            html = (f'<link rel="canonical" href="{url}/">'
                    f'<script type="application/ld+json">{json.dumps(group)}</script>')
            detail = product_detail(html, url, meta)
            detail.update(source_sha256='a'*64, retrieved_at_utc='2026-11-23T02:00:00Z')
            return care_observation(detail)

        care = read()
        self.assertEqual((care['home_wash'], care['max_water_c'], care['dry_clean']), ('hand', 40, 'allowed'))
        group['description'] = '・ドライクリーニング、ウェットクリーニング：可能'
        group['material'] = 'ドライクリーニング（家庭洗濯不可・漂白剤不可・タンブル乾燥不可）'
        care = read()
        self.assertEqual((care['home_wash'], care['dry_clean']), ('prohibited', 'allowed'))
        group['description'] = '・ドライクリーニング：不可'
        self.assertEqual(read()['dry_clean'], 'unknown')
        group.pop('material')
        group['description'] = '洗濯方法：家庭洗濯機×（ドライクリーニングのみ可能）'
        care = read()
        self.assertEqual((care['home_wash'], care['dry_clean']), ('prohibited', 'allowed'))
        group['productGroupID'] = 'WRONG-PRODUCT'
        with self.assertRaises(ValueError):
            read()

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
                'ingredient': '【ブラック】綿100%<br>【グレー】アクリル100％',
                'tagFunctionList': [{'tagName': '抗ピリング'}, {'tagName': '帯電防止'}]}
        data = {'result': 'true', 'resultDtl': {'item': [item]}}
        detail = dot_detail(json.dumps(data), url, request, meta)
        detail.update(source_sha256='b'*64, retrieved_at_utc='2026-11-21T23:00:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['max_water_c'], care['dry_clean']), ('machine', 30, 'allowed'))
        self.assertEqual(detail['function_claims'], ['抗ピリング', '帯電防止'])
        self.assertEqual(detail['composition'], '【ブラック】綿100% 【グレー】アクリル100％')
        item.update(washIcon=None, tagFunctionList=[])
        material_only = dot_detail(json.dumps(data),url,request,meta)
        self.assertNotIn('care_label',material_only)
        self.assertEqual(material_only['composition_evidence'],'OFFICIAL_MATCHING_PRODUCT_TABLE')
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
