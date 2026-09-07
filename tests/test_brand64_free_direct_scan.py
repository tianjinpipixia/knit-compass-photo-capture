import importlib.util
import pathlib
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('free_scan',ROOT/'scripts/run_brand64_free_direct_scan.py')
scan=importlib.util.module_from_spec(spec);spec.loader.exec_module(scan)
META={'brand_name':'ROPÉ PICNIC','adapter':'jun','slug':'rope-picnic','entry_urls':['https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/']}
URL='https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM66000'
def card(slug='rope-picnic',brand='ROPÉ PICNIC',color='08'):
    return f'<div class="content-cassette"><p class="brand-name">{brand}</p><p class="item-name">サイドスリットニット</p><p class="item-price">&yen;5,489</p><p class="item-tag"><span>予約</span></p><a class="content-cassette__link" href="/{slug}/product/tops/knit-sweater/GDM66000?cc={color}"></a></div>'
class Tests(unittest.TestCase):
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
if __name__=='__main__':unittest.main()
