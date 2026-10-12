#!/usr/bin/env python3
"""Validate saved spring coverage without network access or ledger mutations."""
from __future__ import annotations

import argparse
from collections import Counter
from calendar import monthrange
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TERMINAL_STATUSES = frozenset({'VERIFIED_PRODUCTS', 'VERIFIED_NO_PRODUCTS'})
NONTERMINAL_STATUSES = frozenset({'PENDING', 'PARTIAL', 'SOURCE_ACCESS_LIMITED',
                                'SOURCE_OFFLINE_UNVERIFIED'})
APPROVED_ROSTER_BLOB = '727f77fb590ddf639a704b00da188c0ec071d730'
APPROVED_ROSTER_DIGEST = '38495c66a573cf72573bc3897054451835ec2d465d6ee012429506255708c56c'
INITIAL_INVENTORY_ROWS = 277
INITIAL_INVENTORY_DIGEST = 'e5336c1542c53d05d4177fedef488926c0d58eb8f76fb882c2b7c4ff8a5c25bc'
COVERAGE_PATH = 'data/brand-md-monitoring/2026-spring-backfill-coverage.json'


def validate_status_policy(gate):
    for key, expected in (('terminal_month_statuses', TERMINAL_STATUSES),
                          ('nonterminal_month_statuses', NONTERMINAL_STATUSES)):
        values = gate[key]
        assert isinstance(values, list) and len(values) == len(expected) and set(values) == expected, \
            f'completion status policy mismatch: {key}'


def evidence_digest(evidence):
    return sha256(json.dumps(evidence, ensure_ascii=False, sort_keys=True,
                            separators=(',', ':')).encode('utf-8')).hexdigest()


def validate_roster(brands, roster):
    assert roster['format'] == 'KC_SPRING_APPROVED_ROSTER'
    assert roster['scope_id'] == 'KC40-20260930' and roster['status'] == 'LOCKED_OWNER_APPROVED'
    approved = roster['records']
    assert roster['source_blob_sha'] == APPROVED_ROSTER_BLOB, 'approved roster source blob mismatch'
    assert evidence_digest(sorted(approved, key=lambda b: b['brand_id'])) == APPROVED_ROSTER_DIGEST, \
        'approved roster contents changed from owner-approved scope'
    assert len(approved) == roster['target_brand_count'] == 40
    assert len({b['brand_id'] for b in approved}) == 40
    fields = ('brand_id', 'brand_name', 'research_tier')
    assert {tuple(b[k] for k in fields) for b in brands} == {tuple(b[k] for k in fields) for b in approved}, \
        'approved roster ID/name/tier mismatch'
    assert dict(Counter(b['research_tier'] for b in brands)) == roster['tier_counts']


def evidence_counter(brands):
    return Counter((b['brand_id'], month, evidence_digest(e)) for b in brands
                   for month, cell in b['months'].items() for e in cell.get('evidence', []))


def validate_evidence_preservation(brands, inventory, original_audit, previous_coverage):
    assert inventory['format'] == 'KC_SPRING_EVIDENCE_INVENTORY'
    assert len(inventory['entries']) == inventory['evidence_rows']
    assert evidence_digest(inventory['entries'][:INITIAL_INVENTORY_ROWS]) == INITIAL_INVENTORY_DIGEST, \
        'initial evidence inventory rewritten'
    saved = Counter((r['brand_id'], r['month'], r['evidence_sha256']) for r in inventory['entries'])
    current = evidence_counter(brands)
    assert not saved - current, 'preserved evidence deleted or rewritten'
    assert saved == current, 'new evidence must be registered in the preservation inventory'
    if previous_coverage is not None:
        previous = evidence_counter(previous_coverage['brand_month_coverage'])
        assert not previous - current, 'previous-commit evidence deleted or rewritten'
    original = Counter((c['brand_id'], c['month'], a['url'], a['source_kind'])
                       for c in original_audit['cells'] for a in c['evidence_audit'])
    assert sum(original.values()) == original_audit['scope']['evidence_rows']
    sources = Counter((b['brand_id'], month, e['url'], e['source_kind']) for b in brands
                      for month, cell in b['months'].items() for e in cell.get('evidence', []))
    assert not original - sources, 'original audit evidence inventory missing'


def validate_evidence_audit(cell):
    evidence = cell.get('evidence', [])
    audit = cell.get('evidence_audit', [])
    assert len(audit) == len(evidence), 'evidence/audit row count mismatch'
    assert {a['evidence_index'] for a in audit} == set(range(len(evidence))), 'evidence audit indices mismatch'
    for item in audit:
        row = evidence[item['evidence_index']]
        assert item['url'] == row['url'] and item['source_kind'] == row['source_kind'], 'evidence/audit source mismatch'
        assert item['status'] in {'QUALIFYING_PRODUCT', 'REJECTED', 'SUPPLEMENTARY_UNVERIFIED'}


def validate_no_products(cell, brand, month, official_url, now):
    evidence = cell.get('no_products_evidence')
    assert isinstance(evidence, list) and evidence and all(isinstance(e, dict) for e in evidence), \
        'no-products evidence must be a nonempty structured list'
    check = cell.get('last_checked_at')
    assert check and timestamp(check) <= now, 'no-products requires an actual check time'
    assert cell.get('unresolved_reason') is None, 'no-products cannot retain unresolved access or scope issues'
    year, month_number = map(int, month.split('-'))
    start, end = f'{month}-01', f'{month}-{monthrange(year, month_number)[1]:02d}'
    expected_host = urlsplit(official_url).hostname
    for item in evidence:
        assert item.get('brand_id') == brand['brand_id'] and item.get('brand_name') == brand['brand_name'], 'no-products brand mismatch'
        assert item.get('source_kind') == 'OFFICIAL_MONTH_ARCHIVE', 'no-products requires an official monthly archive'
        assert item.get('product_scope') == 'WOMEN_KNIT' and item.get('month') == month, 'no-products scope/month mismatch'
        assert item.get('period_start') == start and item.get('period_end') == end, 'no-products must cover the whole month'
        url_key(item.get('url', ''))
        assert urlsplit(item['url']).hostname == expected_host, 'no-products source is not the approved official host'
        assert item.get('source_status') == 'ONLINE' and item.get('inspection_scope') == 'COMPLETE_MONTH', 'no-products access or completeness not established'
        assert item.get('result') == 'NO_WOMEN_KNIT_PRODUCTS' and item.get('qualifying_product_count') == 0, 'no-products result mismatch'
        assert item.get('checked_at') and timestamp(item['checked_at']) <= timestamp(check) <= now, 'no-products evidence check time missing or future'
        assert timestamp(item['checked_at']).date().isoformat() >= end, 'no-products checked before the month ended'
        assert isinstance(item.get('observed_fact'), str) and item['observed_fact'].strip(), 'no-products observed fact required'
        assert url_key(item['url']) in {url_key(e['url']) for e in cell.get('evidence', [])}, 'no-products original source lineage missing'
        indices = {i for i, e in enumerate(cell.get('evidence', []))
                   if url_key(e['url']) == url_key(item['url']) and e['source_kind'] == item['source_kind']}
        assert any(a['evidence_index'] in indices and a.get('live_content_retrieved') is True
                   and a.get('brand_verification') == 'MATCH_CONFIRMED'
                   and a.get('month_verification') == 'COMPLETE_MONTH_ARCHIVE_CONFIRMED'
                   for a in cell.get('evidence_audit', [])), 'no-products archive retrieval/brand/month audit missing'


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    assert parsed.tzinfo is not None, 'check times must include timezone'
    return parsed


def url_key(value):
    parsed = urlsplit(value)
    assert parsed.scheme == 'https' and parsed.netloc, 'HTTPS source URL required'
    query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.startswith('utm_')
             and k not in {'srsltid', 'fbclid', 'gclid'}]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip('/'),
                      urlencode(sorted(query)), ''))


def validate(coverage, config, ledger, *, approved_roster, evidence_inventory, original_audit,
             previous_coverage=None, now=None):
    now = now or datetime.now(timezone.utc)
    policy = config['retrospective_season_backfill']
    months = policy['completion_gate']['required_months']
    validate_status_policy(policy['completion_gate'])
    terminal = TERMINAL_STATUSES
    allowed = terminal | NONTERMINAL_STATUSES
    source_kinds = set(policy['accepted_source_kinds'])
    brands = coverage['brand_month_coverage']
    assert len(brands) == coverage['approved_brand_count'] == policy['completion_gate']['required_brands']
    assert len({b['brand_id'] for b in brands}) == len(brands)
    validate_roster(brands, approved_roster)
    validate_evidence_preservation(brands, evidence_inventory, original_audit, previous_coverage)
    official_urls = {b['brand_id']: b['source_url'] for b in approved_roster['records']}
    assert coverage['publication_status'] == 'PUBLISH_HOLD'
    assert coverage['human_review_required'] is True
    assert timestamp(coverage['last_updated_at']) <= now, 'future update time'
    records = ledger['records']
    assert coverage['canonical_record_count'] == len(records)
    assert coverage['canonical_counts_by_brand'] == dict(Counter(r['brand_id'] for r in records))
    observed = Counter()
    by_month = {}
    for month in months:
        status_counts = Counter()
        product_count = 0
        for brand in brands:
            assert set(brand['months']) == set(months)
            cell = brand['months'][month]
            assert cell['status'] in allowed
            status_counts[cell['status']] += 1
            observed[cell['status']] += 1
            evidence = cell.get('evidence', [])
            validate_evidence_audit(cell)
            assert cell['official_pages_checked'] == len({url_key(e['url']) for e in evidence}), 'page count must deduplicate URLs'
            check = cell.get('last_checked_at')
            if check:
                assert timestamp(check) <= now, 'future check time'
            chronology = cell.get('check_time_audit', {})
            if chronology:
                assert timestamp(chronology['original_last_checked_at']) > timestamp(chronology['first_recorded_at'])
                assert check != chronology['original_last_checked_at'], 'invalid original check time still active'
            products = cell.get('verified_product_evidence', [])
            assert cell['verified_product_count'] == len(products), 'product count must match qualifying identities'
            product_urls, codes = set(), set()
            for product in products:
                assert product['source_kind'] in source_kinds, 'feature-only source cannot qualify'
                assert product['brand_id'] == brand['brand_id'] and product['brand_name'] == brand['brand_name'], 'brand mismatch'
                assert product['product_scope'] == 'WOMEN_KNIT'
                assert all(product.get(k) is True for k in ('brand_verified', 'knit_verified', 'gender_verified', 'month_verified'))
                key = url_key(product['url'])
                code = product['product_code']
                assert key not in product_urls and code not in codes, 'duplicate product identity'
                product_urls.add(key)
                codes.add(code)
                assert product['published_date'][:7] == month, 'month evidence mismatch'
                assert product['period_evidence']['value'] == product['published_date']
                assert product['period_evidence']['sales_start_date_proven'] is False
                assert check and timestamp(product['checked_at']) <= timestamp(check) <= now
                index = product['original_evidence_index']
                assert url_key(evidence[index]['url']) == key, 'original source lineage missing'
            if cell['status'] == 'VERIFIED_PRODUCTS':
                assert products and cell['unresolved_reason'] is None, 'terminal product cell lacks qualifying evidence'
            elif cell['status'] == 'VERIFIED_NO_PRODUCTS':
                assert not products, 'no-products claim conflicts with qualifying products'
                validate_no_products(cell, brand, month, official_urls[brand['brand_id']], now)
            else:
                assert cell['unresolved_reason'], 'nonterminal reason required'
            product_count += len(products)
        by_month[month] = {
            'total_brand_month_cells': len(brands),
            'terminal_brand_month_cells': sum(status_counts[s] for s in terminal),
            'partial_brand_month_cells': status_counts['PARTIAL'],
            'not_started_brand_month_cells': status_counts['PENDING'],
            'verified_product_count': product_count,
        }
    expected = {
        'total_brand_month_cells': len(brands) * len(months),
        'terminal_brand_month_cells': sum(observed[s] for s in terminal),
        'pending_brand_month_cells': sum(n for s, n in observed.items() if s not in terminal),
        'partial_brand_month_cells': observed['PARTIAL'],
        'not_started_brand_month_cells': observed['PENDING'],
        'fully_completed_brands': sum(all(c['status'] in terminal for c in b['months'].values()) for b in brands),
        'month_verified_brands': sum(any(c['status'] in terminal for c in b['months'].values()) for b in brands),
        'season_evidence_only_brands': sum(bool(b.get('season_evidence')) and not any(c['status'] in terminal for c in b['months'].values()) for b in brands),
        'verified_product_month_observations': sum(m['verified_product_count'] for m in by_month.values()),
        'by_month': by_month,
    }
    for key, value in expected.items():
        assert coverage['summary'][key] == value, f'stale summary: {key}'
    assert coverage['summary']['status'] == ('COMPLETE' if expected['pending_brand_month_cells'] == 0 else 'INCOMPLETE')
    return expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--previous-ref', help='Trusted PR base or push-before commit SHA for history preservation')
    args = parser.parse_args()
    def read(path):
        return json.loads((args.root / path).read_text(encoding='utf-8'))
    config = read('config/brand64-md-monitoring.json')
    policy = config['retrospective_season_backfill']
    previous_coverage = None
    if args.previous_ref:
        assert re.fullmatch(r'[0-9a-f]{40}', args.previous_ref), 'previous-ref must be a full commit SHA'
        previous_coverage = json.loads(subprocess.run(
            ['git', 'show', f'{args.previous_ref}:{COVERAGE_PATH}'], cwd=args.root,
            check=True, capture_output=True, text=True).stdout)
    result = validate(read(policy['coverage_status_path']), config, read(policy['ledger_path']),
                      approved_roster=read(policy['approved_roster_path']),
                      evidence_inventory=read(policy['evidence_inventory_path']),
                      original_audit=read(policy['original_integrity_audit_path']),
                      previous_coverage=previous_coverage)
    print(json.dumps({'status': 'PASS',
                      'history_preservation': 'PREVIOUS_COMMIT_CHECKED' if previous_coverage else 'SNAPSHOT_ONLY',
                      **result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

