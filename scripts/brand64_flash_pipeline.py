"""Durable flash observations, bounded recovery, and independent detail enrichment.

Coverage is certified only for an explicitly audited source scope. Merely finding
cards or exhausting an unrecognised pagination widget never certifies a brand.
"""
import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import json
import hashlib
import pathlib
import re
import time

import run_brand64_free_direct_scan as scan

REQUIRED_SURFACES = {'NEW', 'PREORDER', 'KNIT', 'CARDIGAN'}
FUNCTION = re.compile(r'冷感|遮熱|調温|吸水|速乾|抗菌|防臭|制電|抗ピル|抗起球|UV|UPF|PCM', re.I)
STATE_FILES = ('known-products.json', 'coverage-state.json', 'deep-dive-queue.json',
               'flash-history.json', 'detail-results.json')


def read(path, fallback):
    # Corrupt state must fail visibly, never silently become an empty baseline.
    return json.loads(path.read_text()) if path.exists() else fallback


def recovery_urls(row):
    return list(dict.fromkeys(row.get('pending_page_urls', []) +
                             [e['url'] for e in row.get('errors', []) if e.get('url')]))


def retryable_urls(row):
    urls = list(row.get('pending_page_urls', []))
    for error in row.get('errors', []):
        reason = error['reason']
        if re.search(r'Timeout|timed out|HTTP Error: 5\d\d|HTTPError: HTTP Error 5\d\d|Connection|URLError|OSError|BUDGET_EXHAUSTED', reason):
            if error.get('url'): urls.append(error['url'])
    return list(dict.fromkeys(urls))


def merge_row(previous, row, date):
    same_day = previous and previous.get('observed_date') == date
    old = previous if same_day else {}
    successful = set(row.get('successful_page_urls', []))
    attempted = set(row.get('attempted_page_urls', []))
    merged = {**row, 'observed_date': date, 'last_attempt_at_utc': scan.now()}
    merged['successful_page_urls'] = list(dict.fromkeys(old.get('successful_page_urls', []) + list(successful)))
    merged['attempted_page_urls'] = list(dict.fromkeys(old.get('attempted_page_urls', []) + list(attempted)))
    merged['errors'] = [e for e in old.get('errors', []) if e.get('url') not in attempted] + row['errors']
    outstanding = [u for u in recovery_urls(previous or {}) if u not in successful and u not in attempted]
    merged['pending_page_urls'] = list(dict.fromkeys(outstanding + row['pending_page_urls']))
    items = {i['product_url']: i for i in old.get('surface_items', [])}
    items.update({i['product_url']: i for i in row['surface_items']})
    merged['surface_items'] = list(items.values())
    links = {i['product_url']: i for i in old.get('unverified_link_candidates', [])}
    links.update({i['product_url']: i for i in row.get('unverified_link_candidates', [])})
    merged['unverified_link_candidates'] = list(links.values())
    merged['sources'] = old.get('sources', []) + row.get('sources', [])
    if any(i.get('scope_status') == 'BRAND_AND_KNIT_PATH_MATCHED' for i in items.values()):
        merged['scan_status'] = 'PRODUCTS_OBSERVED'
    return merged


def coverage(row, meta, date):
    reasons = []
    if row.get('observed_date') != date: reasons.append('NOT_CHECKED_TODAY')
    entries = meta.get('entry_urls', [])
    if not entries: reasons.append('NO_CONFIGURED_SOURCES')
    if set(entries) - set(row.get('successful_page_urls', [])): reasons.append('ENTRY_NOT_VERIFIED')
    if row.get('errors'): reasons.append('FETCH_OR_EXTRACTION_FAILED')
    if row.get('pending_page_urls'): reasons.append('PAGES_PENDING')
    # Existing source adapters have no completeness audit. Keep them unverified.
    audit = meta.get('coverage_audit', {})
    if not (audit.get('reviewed_at') and audit.get('evidence_url') and
            audit.get('pagination_verified') is True and
            set(audit.get('entry_urls', [])) == set(entries) and
            REQUIRED_SURFACES <= set(audit.get('surfaces', []))):
        reasons.append('SOURCE_SCOPE_AUDIT_REQUIRED')
    if row.get('unverified_link_candidates'): reasons.append('PRODUCT_SCOPE_REVIEW_REQUIRED')
    return {'status': 'COMPLETE_REGISTERED_SCOPE' if not reasons else 'INCOMPLETE', 'reasons': reasons}


def build_summary(active, sources, rows, date):
    statuses = []
    for bid, name in active.items():
        row = rows.get(bid, {})
        check = coverage(row, sources.get(bid, {}), date)
        current = row.get('observed_date') == date
        count = sum(i.get('scope_status') == 'BRAND_AND_KNIT_PATH_MATCHED' for i in row.get('surface_items', [])) if current else 0
        statuses.append({'brand_id': bid, 'brand_name': name, 'coverage': check,
                         'product_count': count, 'last_attempt_at_utc': row.get('last_attempt_at_utc'),
                         'pending_page_urls': row.get('pending_page_urls', []),
                         'errors': row.get('errors', []),
                         'unverified_link_candidate_count': len(row.get('unverified_link_candidates', [])) if current else 0})
    incomplete = [r['brand_id'] for r in statuses if r['coverage']['status'] != 'COMPLETE_REGISTERED_SCOPE']
    missing = [b for b in active if rows.get(b, {}).get('observed_date') != date]
    return {'format': 'KC_BRAND64_FREE_DIRECT_SCAN', 'schema_version': '2.0',
            'collector': 'CHATGPT_OFFICIAL_DIRECT', 'collection_method': 'DIRECT_HTTP_NO_AI_API',
            'observed_date': date, 'generated_at_utc': scan.now(),
            'active_brand_count': len(active), 'attempted_brand_count': len(active)-len(missing),
            'product_observed_brand_count': sum(r['product_count'] > 0 for r in statuses),
            'product_count': sum(r['product_count'] for r in statuses),
            'complete_brand_count': len(active)-len(incomplete), 'unresolved_brand_ids': incomplete,
            'not_attempted_brand_ids': missing, 'pending_page_count': sum(len(r['pending_page_urls']) for r in statuses),
            'scan_status': 'COMPLETE_REGISTERED_SCOPE' if not incomplete else 'PARTIAL_COVERAGE',
            'ai_api_request_count': 0, 'billing_enabled_by_this_job': False,
            'publication_status': 'PUBLISH_HOLD', 'human_review_required': True,
            'sales_quantity_estimation': 'FORBIDDEN', 'brands': statuses}


def queue_deep(changes, queue, tier, sources, date):
    for item in changes:
        if item['delta_type'] != 'FIRST_OBSERVED_CANDIDATE': continue
        bid = item['brand_id']
        reasons = []
        if bid in tier: reasons.append('PRIORITY_BRAND')
        if FUNCTION.search(item['product_name']): reasons.append('FUNCTION_SIGNAL')
        if not reasons: continue
        key = bid+'|'+item['product_url']
        queue.setdefault(key, {'brand_id': bid, 'product_url': item['product_url'],
                              'product_name': item['product_name'], 'queued_date': date,
                              'reasons': reasons, 'status': 'PENDING', 'attempts': 0})
    for bid, meta in sources.items():
        for url in meta.get('watch_product_urls', []):
            key = bid+'|'+url
            queue.setdefault(key, {'brand_id': bid, 'product_url': url,
                                  'queued_date': date, 'reasons': ['OWNER_WATCH'],
                                  'status': 'PENDING', 'attempts': 0})
    return queue


def markdown(summary, events, deep_queue):
    lines = ['# 新商品速報・巡回確認', f"観測日：{summary['observed_date']}", '',
             f"登録範囲の確認完了：{summary['complete_brand_count']}/{summary['active_brand_count']}ブランド。",
             f"本日観測した商品：{summary['product_count']}件。MD用の蓄積として保持します。",
             '初回発見と発売日は区別します。未確認・未取得を「新商品なし」と判定しません。', '',
             '## 本日初めて見つけた商品（発売日未確認）', '',
             '|ブランド|商品|掲載価格|取得元|', '|---|---|---|---|']
    def safe(value): return str(value or '未確認').replace('|', '／').replace('\n', ' ')
    fresh = [e for e in events if e['delta_type'] == 'FIRST_OBSERVED_CANDIDATE']
    for e in fresh:
        lines.append(f"|{safe(e['brand_name'])}|{safe(e['product_name'])}|{safe(e.get('display_price'))}|[公式商品]({e['product_url']})|")
    if not fresh: lines.append('本日の初回発見記録はありません。巡回未完了の場合、新商品がないことを意味しません。')
    lines += ['', '## ブランド・婦人対象の判定待ちリンク', '']
    for event in events:
        if event['delta_type'] == 'UNVERIFIED_LISTING_CANDIDATE':
            lines.append('- '+safe(event['brand_name'])+'：[候補商品]('+event['product_url']+') '+safe(event['product_name']))
    lines += ['', '## ブランド別の確認状況', '', '|ブランド|確認|本日観測商品|残ページ|', '|---|---|---:|---:|']
    for r in summary['brands']:
        label = '登録範囲を確認' if r['coverage']['status'] == 'COMPLETE_REGISTERED_SCOPE' else '未完了'
        lines.append(f"|{r['brand_name']}|{label}|{r['product_count']}|{len(r['pending_page_urls'])}|")
    labels = {'NOT_CHECKED_TODAY': '当日未確認', 'NO_CONFIGURED_SOURCES': '確認先未設定',
              'ENTRY_NOT_VERIFIED': '入口の取得・解析未完了', 'FETCH_OR_EXTRACTION_FAILED': '取得または解析失敗',
              'PAGES_PENDING': '未取得ページあり', 'SOURCE_SCOPE_AUDIT_REQUIRED': '新着・予約・ニット・カーディガンとページ送りの範囲検証待ち',
              'PRODUCT_SCOPE_REVIEW_REQUIRED': 'ブランド・婦人対象の判定待ち'}
    lines += ['', '## 未確認箇所・再取得対象']
    for r in summary['brands']:
        if not r['coverage']['reasons']: continue
        lines += ['', '### '+r['brand_name'], '／'.join(labels[x] for x in r['coverage']['reasons'])]
        lines += ['- '+u for u in r['pending_page_urls']]
        lines += ['- '+e['reason']+'：'+e.get('url', '未設定') for e in r['errors']]
    waiting = sum(v['status'] != 'COMPLETE' for v in deep_queue.values())
    lines += ['', f'深掘り待ち：{waiting}件。速報は詳細調査の完了を待たず保存します。',
              '詳細・混率・発売日等の不明点は未確認。正式マスター・顧客公開は確認後。']
    return '\n'.join(lines)+'\n'


class Pipeline:
    def __init__(self, out, active, sources, tier, date, stage):
        self.out, self.active, self.sources, self.tier, self.date, self.stage = out, active, sources, tier, date, stage
        # If the durable product baseline is missing, the first successful run is
        # a recovery baseline. Its products must not be reported as newly found.
        self.baseline_initialization = not (out/'known-products.json').exists()
        self.known = read(out/'known-products.json', {})
        self.rows = read(out/'coverage-state.json', {})
        self.queue = read(out/'deep-dive-queue.json', {})
        self.history = read(out/'flash-history.json', {})
        self.details = read(out/'detail-results.json', {})
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        self.run_dir = out/date/(stamp+'-'+stage)
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def checkpoint(self):
        for row in self.rows.values():
            if row.get('observed_date') == self.date:
                row['collector'] = 'CHATGPT_OFFICIAL_DIRECT'
                row['collection_method'] = 'DIRECT_HTTP_NO_AI_API'
        summary = build_summary(self.active, self.sources, self.rows, self.date)
        summary['stage'] = self.stage
        summary['artifact_path'] = str(self.run_dir/'scan.json')
        # History first: a crash before baseline save may duplicate a detection, but
        # must never suppress an event already incorporated into the baseline.
        for name, value in [('flash-history.json', self.history), ('known-products.json', self.known),
                            ('coverage-state.json', self.rows), ('deep-dive-queue.json', self.queue),
                            ('detail-results.json', self.details)]:
            scan.save(self.out/name, value)
        events = [e for e in self.history.values() if e['observed_date'] == self.date]
        candidates = [e for e in events if e['delta_type'] != 'BASELINE_INITIALIZATION']
        summary['first_observed_candidate_count'] = sum(e['delta_type'] == 'FIRST_OBSERVED_CANDIDATE' for e in events)
        summary['candidate_delta_count'] = len(candidates)
        summary['baseline_initialization_count'] = sum(e['delta_type'] == 'BASELINE_INITIALIZATION' for e in events)
        scan.save(self.run_dir/'scan.json', {**summary, 'observations': self.rows, 'candidate_deltas': events})
        scan.save(self.out/'feed.json', {'format': 'KC_BRAND64_OWNER_FLASH', 'schema_version': '1.0',
                  'summary': summary, 'candidates': candidates,
                  'deep_dive_pending_count': sum(v['status'] != 'COMPLETE' for v in self.queue.values())})
        scan.save(self.out/'latest.json', summary)
        scan.save(self.out/'flash-latest.json', {'observed_date': self.date,
                  'collector': 'CHATGPT_OFFICIAL_DIRECT', 'collection_method': 'DIRECT_HTTP_NO_AI_API',
                  'candidates': candidates,
                  'publication_status': 'PUBLISH_HOLD', 'human_review_required': True})
        text = markdown(summary, events, self.queue)
        (self.out/'summary.md').write_text(text)
        (self.run_dir/'summary.md').write_text(text)
        return summary

    def accept(self, row):
        bid = row['brand_id']
        self.rows[bid] = merge_row(self.rows.get(bid), row, self.date)
        self.known, changes = scan.update_baseline(
            [row], self.known, self.date,
            baseline_initialization=self.baseline_initialization)
        for item in row.get('unverified_link_candidates', []):
            identity = 'UNVERIFIED|'+bid+'|'+item['product_url']
            self.history.setdefault(identity, {**item, 'brand_id': bid, 'brand_name': row['brand_name'],
                'observed_date': self.date, 'discovered_at_utc': scan.now(),
                'delta_type': 'UNVERIFIED_LISTING_CANDIDATE', 'is_new_release_confirmed': False,
                'publication_status': 'PUBLISH_HOLD', 'human_review_required': True})
        for change in changes:
            record = {**change, 'observed_date': self.date, 'discovered_at_utc': scan.now(),
                      'research_status': 'FLASH_UNCONFIRMED_DETAILS'}
            identity = self.date+'|'+bid+'|'+change['product_url']+'|'+change['delta_type']
            if change['delta_type'] == 'OBSERVED_FIELD_CHANGE':
                identity += '|'+hashlib.sha256(json.dumps(change, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
            self.history.setdefault(identity, record)
        # Rebuild pending work from the durable event history if an earlier process
        # died after baseline persistence but before queue persistence.
        queue_deep(list(self.history.values()), self.queue, self.tier, self.sources, self.date)
        self.checkpoint()


def interleave_hosts(selected, sources):
    # Do not let four workers wait behind the same host's rate-limit lock.
    groups = {}
    for bid in selected:
        entry = sources.get(bid, {}).get('entry_urls', [''])
        host = scan.urlsplit(entry[0] if entry else '').hostname or bid
        groups.setdefault(host, deque()).append(bid)
    order = []
    while any(groups.values()):
        for queue in groups.values():
            if queue: order.append(queue.popleft())
    return order


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--brand', action='append')
    parser.add_argument('--output-root', default=str(scan.OUT))
    parser.add_argument('--date', default=scan.today())
    parser.add_argument('--stage', choices=['flash', 'retry', 'deep', 'check'], default='flash')
    parser.add_argument('--budget-seconds', type=int, default=180)
    parser.add_argument('--max-pages', type=int, default=4)
    args = parser.parse_args(argv)
    if args.date != scan.today(): parser.error('Live observations cannot be backdated')
    if not 1 <= args.max_pages <= 16 or not 1 <= args.budget_seconds <= 300: parser.error('Bounded execution limits required')
    active = read(scan.ROOT/'config/brand64-active-brands.json', {})['active_brands']
    sources = read(scan.ROOT/'config/brand64-free-direct-sources.json', {})['brands']
    tier = read(scan.ROOT/'config/brand64-md-monitoring.json', {})['tiered_analysis']['tier_a_deep_dive_brand_ids']
    if args.brand and set(args.brand)-set(active): parser.error('Unknown brand')
    selected = [b for b in active if not args.brand or b in args.brand]
    selected.sort(key=lambda b: (b != 'BR-00004', b not in tier, list(active).index(b)))
    pipe = Pipeline(pathlib.Path(args.output_root), active, sources, tier, args.date, args.stage)
    if args.stage == 'check':
        summary = pipe.checkpoint()
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if summary['complete_brand_count'] == len(active) else 1
    deadline = time.monotonic()+args.budget_seconds
    fetch = scan.Fetcher(pipe.run_dir/'evidence', deadline=deadline)
    pipe.checkpoint()  # All 64 brands are visible even before the first request.
    if args.stage in {'flash', 'retry'}:
        def collect(bid):
            meta = sources.get(bid, {'brand_name': active[bid]})
            old = pipe.rows.get(bid, {})
            urls = list(dict.fromkeys(meta.get('entry_urls', [])+recovery_urls(old))) if args.stage == 'flash' else retryable_urls(old)
            try:
                return scan.scan_brand(bid, meta, fetch, page_urls=urls, max_pages=args.max_pages)
            except Exception as exc:
                # Preserve this brand as failed without losing other brands' results.
                return {'brand_id': bid, 'brand_name': active[bid], 'scan_status': 'UNRESOLVED',
                        'surface_items': [], 'sources': [], 'errors': [{'url': u, 'reason': 'UNEXPECTED_COLLECTOR_ERROR: '+str(exc)[:300]} for u in urls],
                        'pending_page_urls': urls, 'successful_page_urls': [], 'attempted_page_urls': []}
        if args.stage == 'retry': selected = [b for b in selected if retryable_urls(pipe.rows.get(b, {}))]
        selected = interleave_hosts(selected, sources)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(collect, bid) for bid in selected]
            for future in as_completed(futures): pipe.accept(future.result())
    else:
        queue_deep(list(pipe.history.values()), pipe.queue, tier, sources, args.date)
        ordered = sorted(pipe.queue.items(), key=lambda kv: (kv[1].get('last_attempt_date', ''), 'OWNER_WATCH' not in kv[1]['reasons'], kv[1]['queued_date'], kv[0]))
        count = 0
        for key, task in ordered:
            if task['brand_id'] not in selected or task['status'] == 'COMPLETE' or task.get('last_attempt_date') == args.date: continue
            if time.monotonic() >= deadline or count >= 8: break
            count += 1; task['attempts'] += 1; task['last_attempt_date'] = args.date
            try:
                body, evidence = fetch(task['product_url'])
                detail = scan.product_detail(body, task['product_url'], sources[task['brand_id']])
                detail.update({'source_sha256': evidence['sha256'], 'retrieved_at_utc': evidence['retrieved_at_utc'],
                               'publication_status': 'PUBLISH_HOLD', 'human_review_required': True})
                pipe.details[key] = detail
                task['status'] = 'COMPLETE'; task.pop('error', None)
            except (OSError, ValueError, TimeoutError) as exc:
                task['status'] = 'REVIEW_REQUIRED'; task['error'] = str(exc)[:300]
            pipe.checkpoint()
    summary = pipe.checkpoint()
    print(json.dumps({k: summary[k] for k in ('stage', 'product_count', 'complete_brand_count', 'pending_page_count')}, ensure_ascii=False))
    # Transport/extraction gaps are recorded; coverage is a separate, strict gate.
    return 0
