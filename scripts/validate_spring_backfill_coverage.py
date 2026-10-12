#!/usr/bin/env python3
"""Validate saved spring coverage without network access or ledger mutations."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


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


def validate(coverage, config, ledger, *, now=None):
    now = now or datetime.now(timezone.utc)
    policy = config['retrospective_season_backfill']
    months = policy['completion_gate']['required_months']
    terminal = set(policy['completion_gate']['terminal_month_statuses'])
    allowed = terminal | set(policy['completion_gate']['nonterminal_month_statuses'])
    source_kinds = set(policy['accepted_source_kinds'])
    brands = coverage['brand_month_coverage']
    assert len(brands) == coverage['approved_brand_count'] == policy['completion_gate']['required_brands']
    assert len({b['brand_id'] for b in brands}) == len(brands)
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
                assert not products and cell.get('no_products_evidence'), 'no-products claim requires explicit research evidence'
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
    args = parser.parse_args()
    def read(path):
        return json.loads((args.root / path).read_text(encoding='utf-8'))
    config = read('config/brand64-md-monitoring.json')
    policy = config['retrospective_season_backfill']
    result = validate(read(policy['coverage_status_path']), config, read(policy['ledger_path']))
    print(json.dumps({'status': 'PASS', **result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
