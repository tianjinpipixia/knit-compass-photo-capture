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
if __name__=='__main__':unittest.main()
