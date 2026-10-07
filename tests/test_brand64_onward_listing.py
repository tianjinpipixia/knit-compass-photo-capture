import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import run_brand64_free_direct_scan as scan
import brand64_flash_pipeline as pipeline

URL = 'https://crosset.onward.co.jp/items?bc=003&gc=2&pp=10&du=2&scc=1004'
META = {'adapter': 'onward-listing', 'brand_name': '組曲', 'brand_code': '003', 'entry_urls': [URL]}


def card(brand='組曲', code='KRWXLW0556', category='1004', gender='', brand_code='003', colour='034', name='【先行予約】シックニット フリル襟付きプルオーバー'):
    data = json.dumps({'code': code, 'brandCode': brand_code, 'smallCategoryCode': category, 'genderCode': gender})
    return f'''<div class="c-item-card" data-web-tracking-item='{data}'>
      <div class="c-item-card__brand">{brand}</div>
      <a class="c-item-card__name-link" href="https://crosset.onward.co.jp/items/{code}?cc={colour}">{name}</a>
      <div class="c-item-card__price">¥13,970</div>
      <div class="c-item-card__badge-upper">NEW 予約商品</div></div>'''


class OnwardListingTests(unittest.TestCase):
    def test_stripe_search_entries_reuse_existing_brand_and_knit_guard(self):
        url = 'https://stripe-club.com/brand/american-holic/search?so=NEW'
        meta = {'adapter': 'stripe', 'slug': 'american-holic', 'brand_name': 'AMERICAN HOLIC'}
        html = '''<div data-basicitemcode="100HA26H0019"><a href="https://stripe-club.com/brand/american-holic/item/100HA26H0019?clr_id=102">AMERICAN HOLIC メタルニットカーディガン</a></div>
            <a href="/brand/other/item/OTHER">Other ニット</a>
            <a href="/brand/american-holic/item/SHIRT">AMERICAN HOLIC シャツ</a>'''
        items = scan.adapters.extract(scan.Document(html), url, meta)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['product_code'], '100HA26H0019')
        self.assertEqual(items[0]['display_price'], '')
        self.assertEqual(items[0]['scope_status'], 'BRAND_AND_KNIT_PATH_MATCHED')

    def test_superseded_errors_are_archived_without_hiding_active_failures(self):
        old = 'https://crosset.onward.co.jp/shop/kumikyoku?du=1'
        error = {'url': old, 'reason': 'redirect error'}
        row = {'errors': [error, {'url': URL, 'reason': 'TimeoutError'}],
               'pending_page_urls': [old, URL], 'surface_items': [],
               'observed_date': scan.today()}
        meta = {**META, 'superseded_entry_urls': [old, URL]}
        pipeline.archive_superseded_sources(row, meta, scan.today())
        self.assertEqual(row['pending_page_urls'], [URL])
        self.assertEqual(row['errors'], [{'url': URL, 'reason': 'TimeoutError'}])
        self.assertEqual(row['superseded_sources'][old]['errors'], [error])
        self.assertTrue(row['superseded_sources'][old]['was_pending'])
        self.assertEqual(pipeline.coverage(row, meta, scan.today())['status'], 'INCOMPLETE')
        pipeline.archive_superseded_sources(row, meta, scan.today())
        self.assertEqual(len(row['superseded_sources'][old]['errors']), 1)
        success = scan.scan_brand('B', META, lambda u: (card(), {'url': u, 'sha256': 'fixture'}))
        merged = pipeline.merge_row(row, success, '2099-01-01')
        self.assertEqual(merged['superseded_sources'], row['superseded_sources'])

    def test_pipeline_restart_preserves_superseded_history_and_known_products(self):
        old = 'https://www.doclasse.com/'
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            scan.save(out/'known-products.json', {'historical': {'first_seen_date': '2026-08-01'}})
            scan.save(out/'coverage-state.json', {'B': {'errors': [{'url': old, 'reason': 'unsupported'}], 'pending_page_urls': [old]}})
            meta = {**META, 'superseded_entry_urls': [old]}
            pipe = pipeline.Pipeline(out, {'B': '組曲'}, {'B': meta}, [], scan.today(), 'flash')
            summary = pipe.checkpoint()
            self.assertEqual(summary['complete_brand_count'], 0)
            restored = pipeline.Pipeline(out, pipe.active, pipe.sources, [], scan.today(), 'retry')
            self.assertIn('historical', restored.known)
            self.assertEqual(pipeline.recovery_urls(restored.rows['B']), [])
            self.assertIn(old, restored.rows['B']['superseded_sources'])

    def test_official_card_fields_and_colour_identity(self):
        items = scan.adapters.extract(scan.Document(card()+card(colour='004')), URL, META)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['product_url'], 'https://crosset.onward.co.jp/items/KRWXLW0556')
        self.assertEqual(items[0]['display_price'], '¥13,970')
        self.assertEqual(items[0]['status_labels'], ['NEW', '予約'])

    def test_wrong_source_scope_is_rejected(self):
        for url in [URL.replace('gc=2', 'gc=1'), URL.replace('bc=003', 'bc=002'),
                    URL.replace('scc=1004', 'scc=1205'), URL.replace('/items?', '/shop/kumikyoku?')]:
            self.assertEqual(scan.adapters.extract(scan.Document(card()), url, META), [])

    def test_wrong_card_brand_gender_category_and_identity_are_rejected(self):
        for html in [card(brand='Other'), card(brand_code='002'), card(gender='1'),
                     card(category='1005'), card(name='ニットワンピース'),
                     card().replace('/items/KRWXLW0556?', '/items/OTHER?'),
                     card().replace('https://crosset.onward.co.jp/items/', 'https://example.com/items/'),
                     card().replace('c-item-card__price', 'unrelated-price')]:
            self.assertEqual(scan.adapters.extract(scan.Document(html), URL, META), [])

    def test_missing_or_malformed_tracking_does_not_infer_scope(self):
        for tracking in ['', 'broken', '[]']:
            html = card().replace(json.dumps({'code': 'KRWXLW0556', 'brandCode': '003', 'smallCategoryCode': '1004', 'genderCode': ''}), tracking)
            self.assertEqual(scan.adapters.extract(scan.Document(html), URL, META), [])

    def test_brand_002_card_is_supported_with_its_own_meta(self):
        items = scan.adapters.extract(scan.Document(card(brand='23区', brand_code='002')), URL.replace('bc=003', 'bc=002'), {**META, 'brand_name': '23区', 'brand_code': '002'})
        self.assertEqual(len(items), 1)

    def test_next_widget_preserves_filters_and_one_page_increment(self):
        def fetch(url):
            return card()+f'''<a class="c-pagination__next" href="{URL}&cp=2">次へ進む</a>
              <a class="c-pagination__next" href="{URL.replace('gc=2', 'gc=1')}&cp=2">次へ進む</a>
              <a class="c-pagination__next" href="{URL}&cp=9">次へ進む</a>''', {'url': url, 'sha256': 'fixture'}
        row = scan.scan_brand('BR-00042', META, fetch, max_pages=1)
        self.assertEqual(row['pending_page_urls'], [URL+'&cp=2'])
        self.assertEqual(pipeline.coverage({**row, 'observed_date': scan.today()}, META, scan.today())['status'], 'INCOMPLETE')

    def test_size_exception_is_narrow_and_still_bounded(self):
        self.assertEqual(scan.source_byte_limit(URL), 8_000_000)
        for url in [URL.replace('bc=003', 'bc=004'), URL.replace('gc=2', 'gc=1'),
                    URL.replace('pp=10', 'pp=30'), URL.replace('scc=1004', 'scc=1205'),
                    URL.replace('crosset.onward.co.jp', 'www.doclasse.com')]:
            self.assertEqual(scan.source_byte_limit(url), 4_000_000)

    def test_fetcher_rejects_oversize_and_redirect_losing_scope(self):
        for final_url, expected in [(URL, 8_000_001), (URL.replace('gc=2', 'gc=1'), 4_000_001)]:
            response = MagicMock(); response.__enter__.return_value = response
            response.url = final_url; response.read.return_value = b'x'*expected
            opener = MagicMock(); opener.open.return_value = response
            with tempfile.TemporaryDirectory() as tmp, patch.object(scan.urllib.request, 'build_opener', return_value=opener):
                with self.assertRaisesRegex(ValueError, 'Source exceeds size limit'):
                    scan.Fetcher(pathlib.Path(tmp))(URL)
                response.read.assert_called_once_with(expected)
                self.assertEqual(list(pathlib.Path(tmp).iterdir()), [])


if __name__ == '__main__': unittest.main()
