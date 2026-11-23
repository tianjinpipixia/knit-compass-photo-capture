import importlib.util
import pathlib
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('free_scan',ROOT/'scripts/run_brand64_free_direct_scan.py')
scan=importlib.util.module_from_spec(spec);spec.loader.exec_module(scan)
META={'brand_name':'ROPÉ PICNIC','adapter':'jun','slug':'rope-picnic','entry_urls':['https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/']}
URL='https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM66000'
def card(slug='rope-picnic',brand='ROPÉ PICNIC',color='08'):
    return f'<div class="content-cassette"><p class="brand-name">{brand}</p><p class="item-name">サイドスリットニット</p><p class="item-price">&yen;5,489</p><p class="item-tag"><span>予約</span></p><a class="content-cassette__link" href="/{slug}/product/tops/knit-sweater/GDM66000?cc={color}"></a></div>'
class Tests(unittest.TestCase):
    def test_seven_brand_diagnostic_preserves_product_source_url_and_hash_binding(self):
        import json
        result=json.loads((ROOT/'data/brand-md-monitoring/diagnostics/2026-10-17-seven-brand-recovery/results.json').read_text())
        self.assertEqual(result['publication_status'],'PUBLISH_HOLD')
        self.assertEqual(result['formal_unprocessed_status'],'OPEN')
        self.assertFalse(result['canonical_or_ledger_files_modified'])
        self.assertEqual(len(result['results']),7)
        for row in result['results']:
            candidate=row['local_candidate']
            evidence={(e['url'],e['sha256']) for e in candidate['evidence']}
            identities=[]
            for product in candidate['products_with_evidence']:
                identities.append(scan.product_identity(product))
                observations=product.get('listing_evidence') or [product]
                for item in observations:
                    self.assertIn((item['source_url'],item['source_sha256']),evidence)
                    self.assertEqual(scan.urlsplit(item['product_url']).scheme,'https')
                    self.assertEqual(scan.urlsplit(item['product_url']).hostname,
                                     scan.urlsplit(item['source_url']).hostname)
            self.assertEqual(len(identities),len(set(identities)))
            self.assertEqual(candidate['products'],len(identities))
            self.assertEqual(candidate['coverage']['status'],'INCOMPLETE')
            self.assertIn('SOURCE_SCOPE_AUDIT_REQUIRED',candidate['coverage']['reasons'])

    def test_jun_data_page_pager_recovers_sequential_pages_and_deduplicates(self):
        source=META['entry_urls'][0]
        def fetch(url):
            page=int(scan.parse_qs(scan.urlsplit(url).query).get('page',['1'])[0])
            # Official 2026-10-17 pager: javascript: links, data-page, empty next arrow.
            pager=(f'<div class="pager-area"><div class="pager-area__pagenumber"><ul>'
                   f'<li><a href="javascript:" data-page="{page+1}">{page+1}</a></li>'
                   f'<li class="next"><a href="javascript:" data-page="{page+1}"></a></li>'
                   '</ul></div></div>') if page<3 else ''
            return card()+card().replace('GDM66000',f'GDM{page}')+pager, {'url':url,'sha256':f'page{page}'}
        row=scan.scan_brand('BR-00004',META,fetch,max_pages=1)
        self.assertEqual(row['pending_page_urls'],[source+'?page=2'])
        row=scan.scan_brand('BR-00004',META,fetch,max_pages=4)
        self.assertEqual(row['attempted_page_urls'],[source,source+'?page=2',source+'?page=3'])
        self.assertEqual(len(row['surface_items']),4)
        self.assertEqual(row['pending_page_urls'],[])
        self.assertTrue(all(i['source_url'] in row['successful_page_urls'] for i in row['surface_items']))
        self.assertTrue(all(i['source_sha256'].startswith('page') for i in row['surface_items']))

    def test_jun_pager_preserves_filters_and_rejects_jumps_or_unscoped_widgets(self):
        source=META['entry_urls'][0]+'?stock=&mode=preorder&page=2'
        def node(target='3',pager=True):
            html=f'<a href="javascript:" data-page="{target}"></a>'
            if pager:html='<div class="pager-area"><ul><li>'+html+'</li></ul></div>'
            return next(n for n in scan.Document(html).root.walk() if n.tag=='a')
        result=scan.jun_next_url(node(),source,META)
        self.assertEqual(scan.parse_qs(scan.urlsplit(result).query,keep_blank_values=True),
                         {'stock':[''],'mode':['preorder'],'page':['3']})
        for target in ['1','2','4','-1','3&mode=sale','abc']:
            self.assertIsNone(scan.jun_next_url(node(target),source,META))
        self.assertIsNone(scan.jun_next_url(node(pager=False),source,META))
        for url in [source.replace('https:','http:'),source.replace('www.junonline.jp','other.example'),
                    source.replace('/rope-picnic/','/vis/'),source+'&page=2',source.replace('page=2','page=x')]:
            self.assertIsNone(scan.jun_next_url(node(),url,META))

    def test_jun_functions_require_matching_product_and_explicit_official_evidence(self):
        import json
        product = {'@type': 'Product', 'name': '対象ニット',
                   'url': URL, 'brand': {'name': META['brand_name']},
                   'offers': {'@type': 'Offer', 'price': 5490}}

        def detail(description='', codes=(), table_sku='GDM66000'):
            icons = ''.join(f'<img data-src="/common/img/sustainable/{code}.png">' for code in codes)
            html = '<script type="application/ld+json">'+json.dumps({**product, 'description': description})+'</script>'
            html += (f'<table><tr><th>品番</th><td>{table_sku}</td></tr>'
                     f'<tr><th>サステナブル・<br>機能</th><td>{icons}</td></tr></table>')
            return scan.product_detail(html, URL, META).get('function_claims', [])

        self.assertEqual(detail('・手洗い可能。', ('MMJ-02', 'UNKNOWN')), ['手洗い可'])
        self.assertEqual(detail(codes=('MMJ-01', 'MFC-900', 'MMJ-01')), ['洗濯機洗い可', '抗ピリング'])
        self.assertEqual(detail('・洗濯機OK：ご自宅でマシンウォッシュが可能。'), ['洗濯機洗い可'])
        self.assertEqual(detail('・アンチピリング：毛羽立ちや毛玉になりにくいアンチピリング加工素材。'), ['抗ピリング'])
        self.assertEqual(detail(codes=('MFC-904',)), ['帯電防止'])
        self.assertEqual(detail('・帯電防止：静電気の発生を抑え、着脱時のストレスを軽減。'), ['帯電防止'])
        self.assertEqual(detail('・洗濯機OK：ご自宅でマシンウォッシュが可能。'
                                ' ・アンチピリング：毛羽立ちや毛玉になりにくいアンチピリング加工素材。',
                                ('MMJ-02',)), ['手洗い可', '抗ピリング'])
        self.assertEqual(detail('ピリングが生じることがあります。手洗い可能ではありません。'
                                '自宅で洗えるかは不明です。アンチピリングではありません。'
                                '静電気が発生する場合があり、帯電防止加工はありません。',
                                ('MMJ-01', 'MFC-900', 'MFC-904'), 'OTHER'), [])

    def test_jun_care_strip_requires_matching_sku_and_reviewed_bytes(self):
        import json
        machine = 'f7b5d20f0ddea2cfc4428dcc8c4ec96f76b8446131a6bb77748fe4789f8ea1b7'
        hand = '543efe09e8128d530f27bbdc0e649005d0998926d8205d3cdc63f70a216f1806'
        product = {'@type':'Product','name':'対象','url':URL,'brand':{'name':META['brand_name']},
                   'offers':{'@type':'Offer','price':5490}}
        def read(asset, digest, sku='GDM66000'):
            markup = '<script type="application/ld+json">'+json.dumps(product)+'</script>'
            markup += (f'<table><tr><th>品番</th><td>{sku}</td></tr><tr><th>洗濯表示</th>'
                       f'<td><img class="laundryicon" src="{asset}"></td></tr></table>')
            return scan.product_detail(markup, URL, META, read_care_image_sha=lambda url:digest).get('care_label')
        a=read('/common/img/sentaku/SC-191.gif', machine)
        self.assertEqual((a['home_wash'],a['dry_clean'],a['dry_solvent']),('machine','allowed','F'))
        b=read('/common/img/sentaku/SE-151.gif', hand)
        self.assertEqual((b['home_wash'],b['dry_clean']),('hand','prohibited'))
        c=read('/common/img/sentaku/SF-202.gif', '3db9b4ae91b0fb088ec598f85fa060521847cbbb770de4fa6d46d2838a90ba35')
        self.assertEqual((c['home_wash'],c['dry_clean'],c['wet_clean']),('prohibited','allowed','prohibited'))
        d=read('/common/img/sentaku/SC-194.gif', '7e863b0667c6b387a7e4597c40ae0c9637c14fd6f8575cde123e080318f20ff7')
        self.assertEqual((d['home_wash'],d['max_water_c'],d['home_cycle'],d['dry_clean'],d['dry_solvent']),
                         ('machine',30,'very_gentle','allowed','F'))
        e=read('/common/img/sentaku/SH-155.gif', '0676efae586ce3447776498fad12f4ab9463dd120cdde153eceb94473ecab6bf')
        self.assertEqual((e['home_wash'],e['max_water_c'],e['dry_clean']),('hand',30,'prohibited'))
        self.assertEqual(read('/common/img/sentaku/SC-194.gif','0'*64)['status'],'unresolved')
        self.assertEqual(read('/common/img/sentaku/SC-191.gif','0'*64)['status'],'unresolved')
        self.assertEqual(read('/common/img/sentaku/UNKNOWN.gif',machine)['status'],'unresolved')
        self.assertIsNone(read('/common/img/sentaku/SC-191.gif',machine,'ANOTHER'))
        self.assertIsNone(read('//another.example/SC-191.gif',machine))

    def test_jun_multiple_strips_preserve_only_shared_care(self):
        import json
        from jun_care_labels import care_observation

        product = {'@type': 'Product', 'name': '対象', 'url': URL, 'brand': {'name': META['brand_name']},
                   'offers': {'@type': 'Offer', 'price': 5490}}
        assets = {
            '/common/img/sentaku/SC-194.gif': '7e863b0667c6b387a7e4597c40ae0c9637c14fd6f8575cde123e080318f20ff7',
            '/common/img/sentaku/SH-194.gif': 'f66d460b1ba99e9d833684dc4457a7f9932fabf8c2c3b9c47d0874fc0ccede23',
        }
        images = ''.join(f'<img class="laundryicon" src="{path}">' for path in assets)
        markup = (f'<script type="application/ld+json">{json.dumps(product)}</script>'
                  '<table><tr><th>品番</th><td>GDM66000</td></tr>'
                  f'<tr><th>洗濯表示</th><td>{images}</td></tr></table>')
        read = lambda url: assets[url.removeprefix('https://www.junonline.jp')]
        detail = scan.product_detail(markup, URL, META, read_care_image_sha=read)
        detail.update(source_sha256='1'*64, retrieved_at_utc='2026-11-23T03:00:00Z')
        care = care_observation(detail)
        self.assertEqual((care['home_wash'], care['max_water_c'], care['dry_clean'], care['dry_solvent']),
                         ('unknown', None, 'allowed', 'F'))
        self.assertEqual(care['image_sha256'], care['images'][0]['image_sha256'])
        self.assertNotIn('image_url', care)
        assets['/common/img/sentaku/SH-194.gif'] = '0'*64
        unresolved = scan.product_detail(markup, URL, META, read_care_image_sha=read)
        self.assertEqual(unresolved['care_label']['status'], 'unresolved')

    def test_non_jun_uses_only_product_bound_care_and_keeps_omitted_dry_unknown(self):
        import json
        from official_care_text import care_from_text
        source='https://www.uniqlo.com/jp/ja/products/E488191-000/00'
        payload={'entity':{'pdpEntity':{'E488191-000-00':{'product':{
            'productId':'E488191-000','name':'ニット','washingInformation':'手洗い可, ドライクリーニング可',
        }}}}}
        meta={'adapter':'fr','brand_name':'UNIQLO'}
        markup=f'<link rel="canonical" href="{source}">'
        markup+='<script>window.__PRELOADED_STATE__ = '+json.dumps(payload,ensure_ascii=False)+';</script>'
        markup+='<section id="productMaterialDescription-content"><p>手洗い可, ドライクリーニング可</p></section>'
        care=scan.product_detail(markup,source,meta)['care_label']
        self.assertEqual((care['home_wash'],care['dry_clean']),('hand','allowed'))
        with self.assertRaises(ValueError):
            scan.product_detail(markup,source.replace('488191','488192'),meta)
        self.assertEqual(care_from_text('手洗い')['dry_clean'],'unknown')
        petroleum = care_from_text('ドライクリーニング（石油系）')
        self.assertEqual((petroleum['home_wash'],petroleum['dry_clean'],petroleum['dry_solvent']),
                         ('unknown','allowed','F'))
        self.assertEqual(care_from_text('ドライ石油系')['dry_solvent'],'F')
        self.assertEqual(care_from_text('ドライクリーニング（石油系）不可')['dry_clean'],'unknown')
        self.assertEqual(care_from_text('家庭洗濯不可、ドライクリーニング不可')['dry_clean'],'prohibited')
        self.assertEqual(care_from_text('洗濯機OK、手洗いのみ')['home_wash'],'unknown')
        self.assertEqual(care_from_text('手洗いかドライクリーニング可かは不明です。')['status'],'unresolved')

        detail='https://www.doclasse.com/item/detail/1_1_32669/008'
        markup='<link rel="canonical" href="https://www.doclasse.com/item/detail/1_1_32669">'
        markup+='<meta property="og:title" content="ニット/DoCLASSE">'
        markup+='<table><tr><th>洗濯表示</th><td>洗濯機可</td></tr></table>'
        markup+='<div class="detailArea__txt__explain"><p>95％以上UVカット</p><p>接触冷感</p></div>'
        markup+='<div class="review"><p>抗菌防臭</p></div>'
        product=scan.product_detail(markup,detail,{'adapter':'doclasse','brand_name':'DoCLASSE'})
        self.assertEqual(product['function_claims'],['UVカット','接触冷感'])
        self.assertEqual(product['care_label']['home_wash'],'machine')

        path='https://www.canshop.jp/ap/item/i/A1CAN000A5QL'
        markup=f'<link rel="canonical" href="{path}"><meta property="og:title" content="Te chichi/ニット">'
        markup+='<dl><dt>洗濯表記</dt><dd>手洗い可 石油系ドライクリーニング</dd></dl>'
        product=scan.product_detail(markup,path,{'adapter':'canshop','brand_name':'Te chichi'})
        self.assertEqual(product['care_label']['dry_clean'],'allowed')
        with self.assertRaises(ValueError):
            scan.product_detail(markup.replace('Te chichi/','別ブランド/'),path,
                                {'adapter':'canshop','brand_name':'Te chichi'})

    def test_product_group_detail_collects_variant_offers(self):
        html = '''<script type="application/ld+json">{
          "@type":"ProductGroup","name":"ウールミンクショートボレロ",
          "url":"https://usagi-online.com/brand/snidel/item/SND0126F0205",
          "brand":{"name":"SNIDEL"},
          "hasVariant":[{"@type":"Product","offers":{"@type":"Offer","price":11440,"priceCurrency":"JPY"}}]
        }</script>'''
        detail = scan.product_detail(html,
            'https://usagi-online.com/brand/snidel/item/SND0126F0205',
            {'brand_name':'SNIDEL'})
        self.assertEqual(detail['product_name'], 'ウールミンクショートボレロ')
        self.assertEqual(detail['offers'][0]['price'], 11440)

    def test_product_group_ignores_related_product_offers(self):
        html='''<script type="application/ld+json">{
          "@type":"ProductGroup","name":"対象ニット",
          "brand":{"name":"SNIDEL"},"url":"https://example.com/target",
          "hasVariant":[{"@type":"Product","offers":{"@type":"Offer","price":11440}}],
          "isRelatedTo":{"@type":"Product","name":"関連商品",
            "offers":{"@type":"Offer","price":999}}
        }</script>'''
        detail=scan.product_detail(html,'https://example.com/target',{'brand_name':'SNIDEL'})
        self.assertEqual([offer['price'] for offer in detail['offers']], [11440])

    def test_product_detail_rejects_url_less_offer_from_other_graph_product(self):
        html='''<script type="application/ld+json">{"@graph":[
          {"@type":"Product","name":"別の商品","brand":{"name":"SNIDEL"},
           "url":"https://example.com/other","offers":{"@type":"Offer","price":999}},
          {"@type":"Product","name":"対象ニット","brand":{"name":"SNIDEL"},
           "url":"https://example.com/target","offers":{"@type":"Offer","price":11440}}
        ]}</script>'''
        detail=scan.product_detail(html,'https://example.com/target',{'brand_name':'SNIDEL'})
        self.assertEqual(detail['product_name'], '対象ニット')
        self.assertEqual([offer['price'] for offer in detail['offers']], [11440])

    def test_jun_dedupes_colors_and_excludes_kids_and_other_brands(self):
        html=card()+card(color='09')+card('rope-picnic-kids','ROPÉ PICNIC KIDS')+card('vis','VIS')
        items=scan.jun_items(scan.Document(html),META['entry_urls'][0],META)
        self.assertEqual(len(items),1);self.assertEqual(items[0]['product_url'],URL)
        self.assertEqual(items[0]['display_price'],'¥5,489');self.assertEqual(items[0]['status_labels'],['予約'])
    def test_script_content_cannot_inject_product_cards(self):
        html='<script>'+card()+'</script><!--'+card()+'-->'
        self.assertEqual(scan.jun_items(scan.Document(html),URL,META),[])
    def test_failed_source_is_unresolved_and_keeps_old_baseline(self):
        with patch.object(scan.urllib.request,'urlopen',side_effect=AssertionError('No AI/network allowed in test')):
            row=scan.scan_brand('BR-00004',META,lambda url:(_ for _ in ()).throw(OSError('offline')))
            self.assertEqual(row['scan_status'],'UNRESOLVED')
            known={'old-product':{'first_seen_date':'2026-08-01'}}
            after,deltas=scan.update_baseline([row],known,'2026-09-07')
            self.assertEqual(after,known);self.assertEqual(deltas,[])
    def test_first_observation_is_not_a_launch_and_repeated_scan_dedupes(self):
        items=scan.jun_items(scan.Document(card()),URL,META)
        rows=[{'brand_id':'BR-00004','brand_name':'ROPÉ PICNIC','surface_items':items}]
        known,deltas=scan.update_baseline(rows,{},'2026-09-07')
        self.assertFalse(deltas[0]['is_new_release_confirmed']);self.assertIsNone(deltas[0]['sales_start_date'])
        after,deltas=scan.update_baseline(rows,known,'2026-09-08');self.assertEqual(deltas,[])
        self.assertEqual(next(iter(after.values()))['first_seen_date'],'2026-09-07')
    def test_generic_links_are_not_confirmed_brand_products(self):
        html='<a href="/item/1">ニットカーディガン</a><a href="https://other.example/item/2">ニット</a>'
        items=scan.generic_items(scan.Document(html),'https://official.example/brand/',META)
        self.assertEqual(len(items),1)
        _,changes=scan.update_baseline([{'brand_id':'X','brand_name':'X','surface_items':items}],{},'2026-09-07')
        self.assertEqual(changes,[])
    def test_product_detail_rejects_related_product_or_wrong_brand(self):
        import json
        product={'@type':'Product','name':'Other','brand':{'name':'VIS'},'offers':{'url':URL,'price':5489}}
        with self.assertRaises(ValueError):scan.product_detail('<script type="application/ld+json">'+json.dumps(product)+'</script>',URL,META)
    def test_collector_has_no_api_key_or_model_dependency(self):
        source=(ROOT/'scripts/run_brand64_free_direct_scan.py').read_text()
        self.assertNotIn('generativelanguage.googleapis.com',source)
        self.assertNotIn('GEMINI_API_KEY',source)
class FamilyAdapters(unittest.TestCase):
    def test_baycrews_saved_absolute_card_urls_and_color_deduplication(self):
        import json
        meta=json.loads((ROOT/'config/brand64-free-direct-sources.json').read_text())['brands']['BR-00077']
        source=meta['entry_urls'][0]
        html=(ROOT/'tests/fixtures/relume-listing-20261001.html').read_text()
        items=scan.adapters.extract(scan.Document(html),source,meta)
        self.assertEqual(len(items),1) # two colour cards for the same product
        item=items[0]
        self.assertEqual(item['product_code'],'26080462867030')
        self.assertEqual(item['product_name'],'《WEB限定追加 / 新色》ダブルニットコントラストプルオーバー')
        self.assertEqual(item['display_price'],'¥10,450')
        self.assertNotIn('?',item['product_url'])
        self.assertEqual(item['scope_status'],'BRAND_AND_KNIT_PATH_MATCHED')
        relative=html.replace('https://baycrews.jp/item/detail/','/item/detail/')
        self.assertEqual(scan.adapters.extract(scan.Document(relative),source,meta),items)
        # The earlier official research used this equivalent, explicit women/category route.
        path_source='https://baycrews.jp/item/list/js-relume/category/cutsew/ladys?q_mccate=231&qPage=0'
        self.assertEqual(len(scan.adapters.extract(scan.Document(html),path_source,meta)),1)

    def test_baycrews_requires_same_host_brand_gender_category_and_card_fields(self):
        import json
        meta=json.loads((ROOT/'config/brand64-free-direct-sources.json').read_text())['brands']['BR-00077']
        source=meta['entry_urls'][0]
        html=(ROOT/'tests/fixtures/relume-listing-20261001.html').read_text()
        for bad in [html.replace('https://baycrews.jp/item/detail/','https://other.example/item/detail/'),
                    html.replace('JOURNAL STANDARD relume','SLOBE IENA'),
                    html.replace('class="itemName"','class="unrecognised"'),
                    html.replace('class="price"','class="unrecognised"')]:
            with self.subTest(bad=bad[:80]):
                self.assertEqual(scan.adapters.extract(scan.Document(bad),source,meta),[])
        for bad_source in [source.replace('q_mtype=1','q_mtype=2'),
                           source.replace('q_mshop=0498','q_mshop=0000'),
                           source.replace('q_mccate=231','q_mccate=999'),
                           'https://baycrews.jp/item/list/js-relume/ladys',
                           'https://baycrews.jp/item/list/js-relume/category/cutsew/ladys?q_mccate=231&q_mtype=2']:
            self.assertEqual(scan.adapters.extract(scan.Document(html),bad_source,meta),[])
        # A neighbouring brand/price must never establish fields for an empty card.
        mixed=html.replace('JOURNAL STANDARD relume','SLOBE IENA')
        mixed+='<li class="item"><a href="/item/detail/js-relume/cutsew/123"></a><div class="brand">JOURNAL STANDARD relume</div></li>'
        self.assertEqual(scan.adapters.extract(scan.Document(mixed),source,meta),[])

    def test_baycrews_empty_next_arrow_is_queued_without_changing_scope(self):
        import json
        meta=json.loads((ROOT/'config/brand64-free-direct-sources.json').read_text())['brands']['BR-00077']
        source=meta['entry_urls'][0]
        html=(ROOT/'tests/fixtures/relume-listing-20261001.html').read_text()
        def fetch(url):
            return html, {'url':url,'sha256':'fixture'}
        row=scan.scan_brand('BR-00077',meta,fetch,page_urls=[source],max_pages=1)
        self.assertEqual(len(row['surface_items']),1)
        self.assertEqual(len(row['pending_page_urls']),1)
        from urllib.parse import parse_qs,urlsplit
        params=parse_qs(urlsplit(row['pending_page_urls'][0]).query)
        self.assertEqual(params['qPage'],['1'])
        self.assertEqual(params['q_mshop'],['0498'])
        for bad in [html.replace('q_mshop=0498&amp;qPage=1','q_mshop=0000&amp;qPage=1'),
                    html.replace('qPage=1','qPage=0'),
                    html.replace('qPage=1','qPage=2'),
                    html.replace('qPage=1','q_mtype=2&amp;qPage=1'),
                    html.replace('https://baycrews.jp/item/list?','https://other.example/item/list?')]:
            row=scan.scan_brand('BR-00077',meta,lambda url:(bad,{'url':url,'sha256':'fixture'}),page_urls=[source],max_pages=1)
            self.assertEqual(row['pending_page_urls'],[])

    def test_baycrews_observation_preserves_separate_reservation_dates(self):
        import json
        meta=json.loads((ROOT/'config/brand64-free-direct-sources.json').read_text())['brands']['BR-00077']
        source=meta['entry_urls'][0]
        html=(ROOT/'tests/fixtures/relume-listing-20261001.html').read_text()
        items=scan.adapters.extract(scan.Document(html),source,meta)
        row={'brand_id':'BR-00077','brand_name':meta['brand_name'],'surface_items':items}
        known,deltas=scan.update_baseline([row],{},'2026-10-02')
        self.assertIsNone(deltas[0]['sales_start_date'])
        self.assertFalse(deltas[0]['is_new_release_confirmed'])
        prior=next(iter(known.values()))
        timing={'reservation_start_date':None,'reservation_start_label':'開始日未確認',
                'expected_delivery_label':'10月上旬','expected_delivery_period':'2026-10',
                'normal_sales_start_date':None,'reservation_timing_status':'DELIVERY_ONLY',
                'reservation_status':'予約掲載確認','expected_delivery':'2026年10月上旬'}
        prior.update(timing)
        after,_=scan.update_baseline([row],known,'2026-10-03')
        updated=next(iter(after.values()))
        for key,value in timing.items():self.assertEqual(updated[key],value)
        self.assertIsNone(updated['sales_start_date'])
        self.assertEqual(updated['publication_status'],'PUBLISH_HOLD')
        self.assertTrue(updated['human_review_required'])

    def test_fr_ignores_men_and_non_knit_recommendations(self):
        import json
        def p(name,gender,pid):
            return {'product':{'name':name,'genderCategory':gender,'sizeGender':gender,'productId':pid,'priceGroup':'00','prices':{'base':{'currency':{'code':'JPY'},'value':3990}}}}
        state={'entity':{'searchEntity':{'a':p('ニット','MEN','E111111-000'),'b':p('シャツ','WOMEN','E222222-000'),'c':p('セーター','WOMEN','E333333-000')}}}
        doc=scan.Document('<script>window.__PRELOADED_STATE__ = '+json.dumps(state)+'</script>')
        items=scan.adapters.extract(doc,'https://www.uniqlo.com/jp/ja/women/sweaters',{'adapter':'fr'})
        self.assertEqual(len(items),1);self.assertEqual(items[0]['product_code'],'E333333-000')
    def test_pal_requires_exact_brand_and_women_filter(self):
        html='<a href="/display/item/GGZ123/?b=gallardagalante"><p class="brand">GALLARDAGALANTE</p><p class="title">ニット</p><p class="price">¥19,800</p></a>'
        meta={'adapter':'pal','brand_name':'GALLARDAGALANTE'}
        self.assertEqual(scan.adapters.extract(scan.Document(html),'https://www.palcloset.jp/display/display/?sex=002',meta),[])
        self.assertEqual(len(scan.adapters.extract(scan.Document(html),'https://www.palcloset.jp/display/display/?sex=001',meta)),1)
        meta['brand_name']='DISCOAT'
        self.assertEqual(scan.adapters.extract(scan.Document(html),'https://www.palcloset.jp/display/display/?sex=001',meta),[])
    def test_pal_listing_without_homepage_css_classes(self):
        html='<a href="/display/item/GGZ123/?cl=0240"><p>GALLARDAGALANTE</p><div class="textOverflow"><p>ニット</p></div><p class="price">¥19,800</p></a>'
        items=scan.adapters.extract(scan.Document(html),'https://www.palcloset.jp/display/display/?sex=001',{'adapter':'pal','brand_name':'GALLARDAGALANTE'})
        self.assertEqual(len(items),1);self.assertEqual(items[0]['product_name'],'ニット')
    def test_verification_page_is_an_access_limit_not_no_products(self):
        row=scan.scan_brand('BR-00004',META,lambda url:('<meta content="URL=?bm-verify=test">',{'url':url,'sha256':'test'}))
        self.assertEqual(row['scan_status'],'SOURCE_ACCESS_LIMITED');self.assertEqual(row['surface_items'],[])
    def test_usagi_color_links_do_not_duplicate_product(self):
        html='<div class="m-item"><p class="m-item-brand">SNIDEL</p><p class="m-item-category">ニット</p><p class="m-item-name">プルオーバー</p><p class="m-item-price">¥9,900</p><a href="/brand/snidel/item/SND123?clr_id=01"></a><a href="/brand/snidel/item/SND123?clr_id=02"></a></div>'
        items=scan.adapters.extract(scan.Document(html),'https://usagi-online.com/brand/snidel/category/AB/AB01/',{'adapter':'usagi','slug':'snidel','brand_name':'SNIDEL'})
        self.assertEqual(len(items),1);self.assertNotIn('?',items[0]['product_url'])
    def test_hidden_shopify_sale_price_is_not_sale_badge(self):
        html='<div class="product-item-meta"><a class="product-item-meta__vendor">NATURAL BEAUTY BASIC</a><a class="product-item-meta__title" href="/products/123">ニット</a><div class="price-list"><span class="visually-hidden">セール価格</span>¥7,491</div></div>'
        items=scan.adapters.extract(scan.Document(html),'https://mix.tokyo/pages/naturalbeautybasic',{'adapter':'shopify','brand_name':'NATURAL BEAUTY BASIC'})
        self.assertEqual(items[0]['status_labels'],[])
    def test_pagination_is_bounded_and_left_pending(self):
        def fetch(url):
            from urllib.parse import parse_qs,urlsplit
            page=int(parse_qs(urlsplit(url).query).get('page',['1'])[0])
            return card()+f'<a rel="next" href="?page={page+1}">次へ</a>',{'url':url,'sha256':'test'}
        row=scan.scan_brand('BR-00004',META,fetch)
        self.assertEqual(len(row['sources']),4);self.assertEqual(len(row['pending_page_urls']),1)
        self.assertEqual(len(row['surface_items']),1)
    def test_known_sales_start_date_survives_later_observation(self):
        items=scan.jun_items(scan.Document(card()),URL,META)
        rows=[{'brand_id':'BR-00004','brand_name':'ROPÉ PICNIC','surface_items':items}]
        known,_=scan.update_baseline(rows,{},'2026-09-07')
        next(iter(known.values()))['sales_start_date']='2026-08-01'
        known,_=scan.update_baseline(rows,known,'2026-09-08')
        self.assertEqual(next(iter(known.values()))['sales_start_date'],'2026-08-01')
    def test_canshop_only_matching_brand_and_no_sales_quantity_fields(self):
        import json
        body=json.dumps({'response':{'docs':[{'bd':'CAN02','bdName':'Te chichi','cd':'A1CAN123','name':'ニット','price':4990,'salesAD':12345},{'bd':'OTHER','bdName':'Other','cd':'X','name':'ニット','price':9}]}})
        items=scan.adapters.extract_json(body,'https://www.canshop.jp/ise/select',{'adapter':'canshop','brand_name':'Te chichi'})
        self.assertEqual(len(items),1);self.assertNotIn('salesAD',items[0])
    def test_global_work_regular_line_excludes_collabs_accessories_and_unisex(self):
        source='https://www.dot-st.com/globalwork/disp/itemlist/?mode=&sort=01&groupNm=0&p=1&refineFlg=true&dispNo=001001&dispNoRadio=001001&goodsType=1'
        def item(code,name):
            return f'<a href="/globalwork/disp/item/{code}/"><p class="item-name">{name}</p><p class="item-price">¥4,990</p></a>'
        html=''.join([
            item('1','透かし編みVネックカーディガン'),
            item('2','高山直子さんコラボ/Hugmeケーブルニット'),
            item('3','NEW ERA/ニットワッチ'),
            item('4','【BEVERLY HILLS POLO CLUB】クルーニット'),
            item('5','【Harry Potter(ハリー・ポッター)】ニットベスト'),
            item('6','ユルリブニットビーニー'),
            item('7','モールニット《ユニセックス》'),
        ])
        meta={'adapter':'dot','slug':'globalwork','brand_name':'GLOBAL WORK',
              'normal_line_only':True,
              'excluded_name_markers':['コラボ','NEW ERA/','【BEVERLY HILLS POLO CLUB】','【Harry Potter']}
        items=scan.adapters.extract(scan.Document(html),source,meta)
        self.assertEqual([x['product_code'] for x in items],['1'])
if __name__=='__main__':unittest.main()
