import importlib.util
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('free_scan',ROOT/'scripts/run_brand64_free_direct_scan.py')
scan=importlib.util.module_from_spec(spec);spec.loader.exec_module(scan)

class RecoveryAdapters(unittest.TestCase):
    def test_stripe_brand_item_without_visible_price_is_verified(self):
        html='''<li><div><a href="https://stripe-club.com/brand/earth1999/item/1001M26G0061?areaid=eb01100"><p>earth music&amp;ecology</p><p>フリルトリムニットカーディガン</p></a></div></li>'''
        items=scan.adapters.extract(scan.Document(html),'https://stripe-club.com/brand/earth1999/',{
            'adapter':'stripe','brand_name':'earth music&ecology','slug':'earth1999'})
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['product_code'],'1001M26G0061')
        self.assertEqual(items[0]['display_price'],'')
        self.assertEqual(items[0]['scope_status'],'BRAND_AND_KNIT_PATH_MATCHED')

    def test_stripe_still_rejects_wrong_brand_or_non_knit(self):
        html='''<li><a href="https://stripe-club.com/brand/earth1999/item/A"><p>Green Parks</p><p>ニット</p></a></li><li><a href="https://stripe-club.com/brand/earth1999/item/B"><p>earth music&amp;ecology</p><p>シャツ</p></a></li>'''
        items=scan.adapters.extract(scan.Document(html),'https://stripe-club.com/brand/earth1999/',{
            'adapter':'stripe','brand_name':'earth music&ecology','slug':'earth1999'})
        self.assertEqual(items,[])

    def test_sense_brand_page_card_requires_official_brand_and_knit(self):
        html='''<div class="block-thumbnail-t--goods"><a href="/shop/g/gAA26330-2021013/?goods=x"><div class="block-thumbnail-t--goods-label">SENSE OF PLACE</div><div class="block-thumbnail-t--goods-name"><p>『洗濯可』ローゲージスラブニット</p></div><div class="block-thumbnail-t--price-infos"><div>¥6,050</div></div></a></div>'''
        items=scan.adapters.extract(scan.Document(html),'https://www.urban-research.jp/shop/label/sense-of-place/',{'brand_name':'SENSE OF PLACE'})
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['product_code'],'gAA26330-2021013')
        self.assertEqual(items[0]['display_price'],'¥6,050')

if __name__=='__main__':unittest.main()
