import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import brand64_flash_pipeline as pipeline
import publish_brand64_flash_feed as publisher
import run_brand64_free_direct_scan as scan

URL = 'https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/'
META = {'brand_name': 'ROPÉ PICNIC', 'adapter': 'jun', 'slug': 'rope-picnic', 'entry_urls': [URL]}
DATE = scan.today()


def card(code='GDM66000'):
    return f'<div class="content-cassette"><p class="brand-name">ROPÉ PICNIC</p><p class="item-name">冷感ニット</p><a class="content-cassette__link" href="{URL}{code}"></a></div>'


def fetch(url):
    page = int(dict(scan.parse_qsl(scan.urlsplit(url).query)).get('page', 1))
    more = f'<a rel="next" href="?page={page+1}">次へ</a>' if page < 6 else ''
    return card('GDM'+str(page))+more, {'url': url, 'sha256': 'fixture', 'retrieved_at_utc': scan.now()}


class FlashPipelineTests(unittest.TestCase):
    def test_first_four_pages_then_recovery_collects_pages_five_and_six(self):
        first = scan.scan_brand('B', META, fetch)
        state = pipeline.merge_row(None, first, DATE)
        second = scan.scan_brand('B', META, fetch, page_urls=pipeline.retryable_urls(state), max_pages=12)
        state = pipeline.merge_row(state, second, DATE)
        self.assertEqual(len(state['surface_items']), 6)
        self.assertEqual(state['pending_page_urls'], [])
        # No assumption that the absence of a next link proves all new/preorder surfaces.
        self.assertEqual(pipeline.coverage(state, META, DATE)['status'], 'INCOMPLETE')

    def test_resume_survives_new_process_and_new_day(self):
        first = pipeline.merge_row(None, scan.scan_brand('B', META, fetch), DATE)
        old_date = (scan.dt.date.fromisoformat(DATE)-scan.dt.timedelta(days=1)).isoformat()
        first['observed_date'] = old_date
        today_row = scan.scan_brand('B', META, lambda u: (card(), {'url': u, 'sha256': 'today'}))
        state = pipeline.merge_row(json.loads(json.dumps(first)), today_row, DATE)
        self.assertIn(URL+'?page=5', pipeline.recovery_urls(state))
        self.assertEqual(len(state['surface_items']), 1)  # Yesterday's cards are not today's observations.

    def test_flash_never_fetches_watched_product_detail(self):
        seen = []
        meta = {**META, 'watch_product_urls': [URL+'GDM66000']}
        def local_fetch(url):
            seen.append(url)
            return card(), {'url': url, 'sha256': 'fixture'}
        scan.scan_brand('B', meta, local_fetch)
        self.assertEqual(seen, [URL])

    def test_transient_failure_recovers_but_access_challenge_is_not_retried_same_run(self):
        row = {'errors': [{'url': URL, 'reason': 'URLError: timed out'},
                          {'url': URL+'?page=2', 'reason': 'SOURCE_ACCESS_CHALLENGE'}], 'pending_page_urls': []}
        self.assertEqual(pipeline.retryable_urls(row), [URL])
        self.assertEqual(len(pipeline.recovery_urls(row)), 2)
        previous = {**row, 'observed_date': DATE, 'surface_items': []}
        success = scan.scan_brand('B', META, lambda u: (card(), {'url': u, 'sha256': 'fixture'}))
        merged = pipeline.merge_row(previous, success, DATE)
        self.assertEqual(len(merged['errors']), 1)
        self.assertIn('SOURCE_ACCESS_CHALLENGE', merged['errors'][0]['reason'])

    def test_39_or_64_brands_with_cards_cannot_pass_without_source_scope_audit(self):
        active = {str(i): str(i) for i in range(64)}
        rows = {bid: {'observed_date': DATE, 'surface_items': [{'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED'}], 'successful_page_urls': [URL]} for bid in active}
        summary = pipeline.build_summary(active, {bid: META for bid in active}, rows, DATE)
        self.assertEqual(summary['product_observed_brand_count'], 64)
        self.assertEqual(summary['complete_brand_count'], 0)
        self.assertEqual(len(summary['unresolved_brand_ids']), 64)

    def test_audit_cannot_cover_a_different_set_of_urls_or_stale_day(self):
        row = pipeline.merge_row(None, scan.scan_brand('B', META, lambda u: (card(), {'url': u, 'sha256': 'fixture'})), DATE)
        audit = {'reviewed_at': DATE, 'evidence_url': URL, 'pagination_verified': True,
                 'entry_urls': [URL], 'surfaces': ['NEW', 'PREORDER', 'KNIT', 'CARDIGAN']}
        meta = {**META, 'coverage_audit': audit}
        self.assertEqual(pipeline.coverage(row, meta, DATE)['status'], 'COMPLETE_REGISTERED_SCOPE')
        self.assertEqual(pipeline.coverage(row, meta, '2099-01-01')['status'], 'INCOMPLETE')
        self.assertEqual(pipeline.coverage(row, {**meta, 'entry_urls': [URL, URL+'?page=2']}, DATE)['status'], 'INCOMPLETE')

    def test_partial_checkpoint_restores_flash_baseline_and_deep_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            p = pipeline.Pipeline(out, {'B': 'ROPÉ PICNIC', 'C': 'Other'}, {'B': META}, ['B'], DATE, 'flash')
            row = scan.scan_brand('B', META, lambda u: (card(), {'url': u, 'sha256': 'fixture'}))
            p.accept(row)
            restarted = pipeline.Pipeline(out, p.active, p.sources, p.tier, DATE, 'retry')
            restarted.accept(row)
            self.assertEqual(len(restarted.history), 1)
            self.assertEqual(len(restarted.queue), 1)
            report = json.loads((out/'latest.json').read_text())
            self.assertEqual(report['not_attempted_brand_ids'], ['C'])
            self.assertEqual(report['first_observed_candidate_count'], 1)
            self.assertEqual(next(iter(restarted.known.values()))['first_seen_date'], DATE)
            self.assertFalse(next(iter(restarted.history.values()))['is_new_release_confirmed'])
            self.assertIn('GDM66000', (out/'summary.md').read_text())

    def test_failures_do_not_delete_md_baseline_or_report_no_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pipeline.Pipeline(pathlib.Path(tmp), {'B': 'ROPÉ PICNIC'}, {'B': META}, [], DATE, 'flash')
            p.known = {'old': {'first_seen_date': '2026-08-01', 'composition': 'cotton'}}
            row = scan.scan_brand('B', META, lambda u: (_ for _ in ()).throw(OSError('offline')))
            p.accept(row)
            self.assertIn('old', p.known)
            summary = p.checkpoint()
            self.assertEqual(summary['scan_status'], 'PARTIAL_COVERAGE')
            self.assertEqual(summary['product_count'], 0)
            self.assertIn(URL, pipeline.recovery_urls(p.rows['B']))

    def test_details_do_not_filter_nonpriority_flash(self):
        changes = [{'brand_id': 'B', 'product_url': URL+'one', 'product_name': '通常ニット', 'delta_type': 'FIRST_OBSERVED_CANDIDATE'},
                   {'brand_id': 'C', 'product_url': URL+'two', 'product_name': '冷感ニット', 'delta_type': 'FIRST_OBSERVED_CANDIDATE'}]
        queue = pipeline.queue_deep(changes, {}, [], {}, DATE)
        self.assertEqual(list(queue), ['C|'+URL+'two'])
        self.assertEqual(len(changes), 2)

    def test_budget_exhaustion_keeps_pending_pages_without_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(scan.urllib.request, 'build_opener', side_effect=AssertionError('network')):
            row = scan.scan_brand('B', META, scan.Fetcher(pathlib.Path(tmp), deadline=0))
            self.assertIn(URL, pipeline.retryable_urls(row))
            self.assertEqual(row['scan_status'], 'UNRESOLVED')

    def test_json_pagination_does_not_stop_at_first_100_rows(self):
        url = 'https://www.canshop.jp/ise/select?rows=100&fq=bd%3ACAN02'
        def json_fetch(source):
            start = int(dict(scan.parse_qsl(scan.urlsplit(source).query)).get('start', 0))
            body = json.dumps({'response': {'numFound': 2, 'start': start, 'docs': [{'bd': 'CAN02', 'bdName': 'Te chichi', 'cd': 'X'+str(start), 'name': 'ニット', 'price': 4990}]}})
            return body, {'url': source, 'sha256': 'fixture'}
        meta = {'adapter': 'canshop', 'brand_name': 'Te chichi', 'entry_urls': [url]}
        row = scan.scan_brand('B', meta, json_fetch)
        self.assertEqual(len(row['surface_items']), 2)
        self.assertEqual(len(row['attempted_page_urls']), 2)
        self.assertEqual(row['pending_page_urls'], [])

    def test_unverified_links_are_saved_in_flash_without_inflating_md_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pipeline.Pipeline(pathlib.Path(tmp), {'B': 'Example'}, {}, [], DATE, 'flash')
            row = {'brand_id': 'B', 'brand_name': 'Example', 'scan_status': 'LINK_CANDIDATES_OBSERVED',
                   'surface_items': [], 'unverified_link_candidates': [{'product_url': URL+'X', 'product_name': 'ニット'}],
                   'errors': [], 'pending_page_urls': []}
            p.accept(row)
            summary = p.checkpoint()
            self.assertEqual(summary['product_count'], 0)
            self.assertEqual(len(p.history), 1)
            self.assertEqual(len(p.known), 0)
            self.assertIn(URL+'X', (pathlib.Path(tmp)/'summary.md').read_text())

    def test_entrypoint_stages_persist_and_deep_failure_does_not_lose_flash(self):
        with tempfile.TemporaryDirectory() as tmp:
            def stub_fetch(url):
                if url.rstrip('/').split('/')[-1].startswith('GDM'):
                    raise ValueError('Detail unavailable')
                return fetch(url)
            args = ['--brand', 'BR-00004', '--output-root', tmp]
            with patch.object(scan, 'Fetcher', return_value=stub_fetch):
                self.assertEqual(pipeline.run(args+['--stage', 'flash']), 0)
                first = json.loads((pathlib.Path(tmp)/'flash-latest.json').read_text())
                self.assertGreater(len(first['candidates']), 0)
                self.assertEqual(pipeline.run(args+['--stage', 'retry', '--max-pages', '12']), 0)
                before_deep = (pathlib.Path(tmp)/'flash-latest.json').read_text()
                self.assertEqual(pipeline.run(args+['--stage', 'deep']), 0)
                self.assertEqual((pathlib.Path(tmp)/'flash-latest.json').read_text(), before_deep)
                queue = json.loads((pathlib.Path(tmp)/'deep-dive-queue.json').read_text())
                self.assertTrue(any(q['status']=='REVIEW_REQUIRED' for q in queue.values()))
                with patch('builtins.print'):
                    self.assertEqual(pipeline.run(args+['--stage', 'check']), 1)
                summary = json.loads((pathlib.Path(tmp)/'latest.json').read_text())
                self.assertEqual(len(summary['brands']), 64)
                self.assertEqual(len(summary['not_attempted_brand_ids']), 63)

    def test_hosts_are_interleaved_without_dropping_brands(self):
        ids=['A','B','C','D','E']
        sources={b:{'entry_urls':['https://'+host+'/']} for b,host in zip(ids,['one.example','one.example','one.example','two.example','three.example'])}
        order=pipeline.interleave_hosts(ids,sources)
        self.assertEqual(order,['A','D','E','B','C'])
        self.assertEqual(set(order),set(ids))

    def test_observed_product_export_preserves_count_without_formal_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            coverage = {
                'BR-00004': {
                    'brand_id': 'BR-00004',
                    'brand_name': 'ROPÉ PICNIC',
                    'surface_items': [
                        {'product_name': '冷感ニット', 'product_url': URL+'GDM66000', 'product_code': 'GDM66000',
                         'display_price': '¥4,994', 'status_labels': ['NEW'], 'source_url': URL,
                         'evidence_level': 'OFFICIAL_LISTING_CARD', 'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED'},
                        {'product_name': 'UVカーディガン', 'product_url': URL+'GDK00001', 'product_code': 'GDK00001',
                         'display_price': '¥5,489', 'status_labels': [], 'source_url': URL,
                         'evidence_level': 'OFFICIAL_LISTING_CARD', 'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED'},
                    ],
                },
            }
            (out/'coverage-state.json').write_text(json.dumps(coverage))
            (out/'latest.json').write_text(json.dumps({
                'observed_date': DATE,
                'active_brand_count': 64,
                'attempted_brand_count': 64,
                'product_observed_brand_count': 1,
                'product_count': 2,
                'scan_status': 'PARTIAL_COVERAGE',
            }))
            generated = publisher.build_observed_product_shards(out)
            self.assertIn('observed-products/manifest.json', generated)
            manifest = json.loads((out/'observed-products/manifest.json').read_text())
            brand = json.loads((out/'observed-products/BR-00004.json').read_text())
            self.assertEqual(manifest['observed_product_count'], 2)
            self.assertEqual(manifest['product_observed_brand_count'], 1)
            self.assertFalse(manifest['formal_product_registration'])
            self.assertEqual(brand['product_count'], 2)
            self.assertFalse(brand['formal_product_registration'])
            self.assertIsNone(brand['records'][0].get('sales_start_date'))

    def test_observed_product_export_refuses_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            (out/'coverage-state.json').write_text(json.dumps({
                'BR-00004': {'brand_name': 'ROPÉ PICNIC', 'surface_items': [{'product_name': '冷感ニット'}]},
            }))
            (out/'latest.json').write_text(json.dumps({
                'observed_date': DATE,
                'active_brand_count': 64,
                'attempted_brand_count': 64,
                'product_observed_brand_count': 1,
                'product_count': 2,
                'scan_status': 'PARTIAL_COVERAGE',
            }))
            with self.assertRaisesRegex(ValueError, 'Observed product export mismatch'):
                publisher.build_observed_product_shards(out)

    def test_corrupt_baseline_is_not_silently_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            (out/'known-products.json').write_text('{broken')
            with self.assertRaises(json.JSONDecodeError):
                pipeline.Pipeline(out, {}, {}, [], DATE, 'flash')


if __name__ == '__main__': unittest.main()
