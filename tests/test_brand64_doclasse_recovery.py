import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import run_brand64_free_direct_scan as scan
import brand64_flash_pipeline as pipeline

URL = 'https://www.doclasse.com/item?brand_id=1&category_id=12'
META = {'adapter': 'doclasse', 'brand_name': 'DoCLASSE', 'entry_urls': [URL]}


def card(code='33211', colour='030', gender='レディース', name='シルキーレーヨン・Vネックニット', category='レディース/セーター・ニット/vネック'):
    # Fields and markup from official category HTML retrieved 2026-10-07.
    return f'''<div class="item_archive__list" data-ga_ec_goods_id="{code}"
      data-ga_ec_goods_brand="{gender}" data-ga_ec_goods_category="{category}">
      <div class="iconList"><span>new</span></div>
      <h2 class="goodsNameWrapper"><a class="goodsDetailLink" href="/item/detail/1_1_{code}/{colour}">{name}</a></h2>
      <p class="price"><span>¥3,490</span><span>￥3,839</span></p></div>'''


class RecoveryTests(unittest.TestCase):
    def test_womens_category_card_and_colour_deduplication(self):
        items = scan.adapters.extract(scan.Document(card()+card(colour='090')), URL, META)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['product_code'], '33211')
        self.assertEqual(items[0]['display_price'], '¥3,490 / ￥3,839')
        self.assertEqual(items[0]['status_labels'], ['NEW'])
        self.assertEqual(items[0]['scope_status'], 'BRAND_AND_KNIT_PATH_MATCHED')

    def test_homepage_other_brand_or_gender_cannot_establish_scope(self):
        for url in ['https://www.doclasse.com/', URL.replace('brand_id=1', 'brand_id=2'), URL.replace('category_id=12', 'category_id=38')]:
            self.assertEqual(scan.adapters.extract(scan.Document(card()), url, META), [])
        self.assertEqual(scan.adapters.extract(scan.Document(card(gender='メンズ')), URL, META), [])
        self.assertEqual(scan.adapters.extract(scan.Document(card()), URL, {**META, 'brand_name': 'Other'}), [])

    def test_rejects_accessories_and_mismatched_identity_or_host(self):
        for html in [card(name='ニットワンピース'), card(category='レディース/ニット帽'),
                     card().replace('/1_1_33211/', '/1_1_99999/'),
                     card().replace('href="/item/', 'href="https://example.com/item/'),
                     card().replace('class="price"', 'class="unrelated-price"')]:
            self.assertEqual(scan.adapters.extract(scan.Document(html), URL, META), [])

    def test_category_scope_supports_name_without_knit_word(self):
        items = scan.adapters.extract(scan.Document(card(name='マシュマロウール100・リブタートル')), URL, META)
        self.assertEqual(len(items), 1)

    def test_pagination_retains_scope_and_pending_pages(self):
        def fetch(url):
            return card()+'''<a rel="next" href="?brand_id=1&category_id=12&page=2"></a>
                <a rel="next" href="?brand_id=2&category_id=12&page=2"></a>
                <a rel="next" href="?brand_id=1&category_id=11&page=2"></a>
                <a rel="next" href="?brand_id=1&category_id=12&page=9"></a>''', {'url': url, 'sha256': 'fixture'}
        row = scan.scan_brand('BR-00018', META, fetch, max_pages=1)
        self.assertEqual(row['pending_page_urls'], [URL+'&page=2'])
        self.assertEqual(pipeline.coverage({**row, 'observed_date': scan.today()}, META, scan.today())['status'], 'INCOMPLETE')

    def test_blocked_pending_pages_remain_saved_but_not_retried(self):
        blocked = ['HTTPError: HTTP Error 403: Forbidden', 'HTTPError: HTTP Error 429: Too Many Requests',
                   'SOURCE_ACCESS_CHALLENGE', 'NO_SUPPORTED_PRODUCT_CARDS_OR_DYNAMIC_PAGE',
                   'ValueError: Source exceeds size limit', 'HTTPError: HTTP Error 302: redirect error']
        row = {'pending_page_urls': ['https://example.com/'+str(i) for i in range(len(blocked))]+[URL],
               'errors': [{'url': 'https://example.com/'+str(i), 'reason': reason} for i, reason in enumerate(blocked)]+
                         [{'url': URL, 'reason': 'TimeoutError: timed out'}]}
        self.assertEqual(pipeline.retryable_urls(row), [URL])
        self.assertEqual(len(pipeline.recovery_urls(row)), len(blocked)+1)
        self.assertEqual(len(row['pending_page_urls']), len(blocked)+1)


if __name__ == '__main__': unittest.main()
