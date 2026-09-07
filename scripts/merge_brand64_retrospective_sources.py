#!/usr/bin/env python3
"""Merge saved Brand64 retrospective product evidence into the durable cumulative baseline.

Daily direct observations and retrospective research share one identity key:
`brand_id|product_url`. Historical evidence enriches an existing current record but
never overwrites fresher daily fields. New historical-only records remain internal,
PUBLISH_HOLD and HUMAN_REVIEW_REQUIRED.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit

COUNTED_SCOPE_STATUS = 'BRAND_AND_KNIT_PATH_MATCHED'
TARGET_MONTHS = {f'2026-{month:02d}' for month in range(4, 10)}
OFFICIAL_MARKERS = ('OFFICIAL', '公式商品', '公式個別', 'OFFICIAL_PRODUCT_PAGE')


def load_json(path: Path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def read_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def canonical_url(value: str) -> str:
    value = str(value or '').strip()
    if not value.startswith(('https://', 'http://')):
        return ''
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip('/') or '/', '', ''))


def date_value(value):
    value = str(value or '')[:10]
    try:
        dt.date.fromisoformat(value)
        return value
    except ValueError:
        return None


def month_value(value):
    date = date_value(value)
    return date[:7] if date else None


def first_date_in_text(value):
    match = re.search(r'2026-\d{2}-\d{2}', str(value or ''))
    return date_value(match.group(0)) if match else None


def price_text(record):
    for key in ('observed_price_jpy', 'observed_price_yen', 'sale_price_jpy', 'sale_price_yen', 'regular_price_jpy', 'regular_price_yen'):
        value = record.get(key)
        if isinstance(value, (int, float)) and value:
            return f'¥{int(value):,}'
    value = record.get('price') or record.get('display_price')
    if value and value not in ('NOT AVAILABLE', 'null'):
        return str(value).replace('JPY ', '¥')
    return ''


def list_value(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if not value or value in ('NOT AVAILABLE', '公式機能表示なし'):
        return []
    return [part.strip() for part in re.split(r'[;/／]', str(value)) if part.strip()]


def record_url(record):
    return canonical_url(record.get('product_url') or record.get('official_product_url') or record.get('official_url'))


def brand_name(record):
    return record.get('brand_name') or record.get('brand') or ''


def source_is_official(record, manual=False, spring=False):
    if manual or spring:
        return True
    text = ' '.join(str(record.get(key) or '') for key in ('source_type', 'source_status', 'source_kind', 'evidence_note'))
    return any(marker in text for marker in OFFICIAL_MARKERS)


def normalize_record(record, source_path, source_snapshot_date=None, manual=False, spring=False):
    url = record_url(record)
    bid = str(record.get('brand_id') or '')
    if not bid or not url:
        return None
    if record.get('eligible_for_cumulative') is False:
        return {'scope_review_only': True, 'brand_id': bid, 'product_url': url, 'source_path': source_path}
    if not source_is_official(record, manual=manual, spring=spring):
        return None

    snapshot_date = (
        date_value(record.get('snapshot_date'))
        or date_value(record.get('observed_date'))
        or date_value(record.get('backfill_observation_date'))
        or date_value(record.get('first_backfill_observation_date'))
        or date_value(record.get('last_verified_date'))
        or date_value(record.get('confirmed_at'))
        or date_value(source_snapshot_date)
    )
    snapshot_month = month_value(snapshot_date)
    evidence_date = date_value(record.get('source_date')) or first_date_in_text(record.get('notes'))
    evidence_month = month_value(evidence_date)
    months = set(record.get('retrospective_months') or [])
    if snapshot_month in TARGET_MONTHS:
        months.add(snapshot_month)
    if evidence_month in TARGET_MONTHS:
        months.add(evidence_month)

    composition = record.get('material_composition') or record.get('composition_raw') or record.get('composition') or ''
    functions = list_value(record.get('function_claims') or record.get('functions') or record.get('function'))
    design = record.get('confirmed_design') or record.get('knit_structure') or record.get('evidence_note') or ''
    status = record.get('release_status') or record.get('launch_status') or record.get('sales_status') or ''

    return {
        'brand_id': bid,
        'brand_name': brand_name(record) or bid,
        'product_name': record.get('product_name') or '',
        'product_url': url,
        'product_code': record.get('product_code') or record.get('product_no') or '',
        'display_price': price_text(record),
        'status_labels': list_value(status),
        'source_url': url,
        'evidence_level': 'OFFICIAL_RETROSPECTIVE_PRODUCT_PAGE',
        'scope_status': COUNTED_SCOPE_STATUS,
        'snapshot_date': snapshot_date,
        'retrospective_months': sorted(months),
        'period_evidence_date': evidence_date,
        'material_composition': composition,
        'function_claims': functions,
        'confirmed_design': design,
        'season_release': record.get('season_release') or record.get('season') or '',
        'regular_price_jpy': record.get('regular_price_jpy') or record.get('regular_price_yen'),
        'sale_price_jpy': record.get('sale_price_jpy') or record.get('sale_price_yen') or record.get('observed_price_jpy'),
        'source_path': source_path,
        'source_record_scope': record.get('record_scope') or record.get('observation_kind') or 'RETROSPECTIVE_OBSERVATION',
    }


def merge_list(existing, incoming):
    return list(dict.fromkeys([*(existing or []), *(incoming or [])]))


def merge_one(known, incoming):
    key = incoming['brand_id'] + '|' + incoming['product_url']
    before = known.get(key)
    evidence = {
        'source_path': incoming['source_path'],
        'snapshot_date': incoming.get('snapshot_date'),
        'retrospective_months': incoming.get('retrospective_months', []),
        'period_evidence_date': incoming.get('period_evidence_date'),
        'source_record_scope': incoming.get('source_record_scope'),
    }
    if before:
        merged = dict(before)
        for field in ('product_name', 'product_code', 'display_price', 'material_composition', 'confirmed_design', 'season_release'):
            if not merged.get(field) and incoming.get(field):
                merged[field] = incoming[field]
        merged['function_claims'] = merge_list(merged.get('function_claims'), incoming.get('function_claims'))
        merged['retrospective_months'] = merge_list(merged.get('retrospective_months'), incoming.get('retrospective_months'))
        merged['retrospective_sources'] = merge_list(merged.get('retrospective_sources'), [incoming['source_path']])
        existing_evidence = merged.get('retrospective_evidence') or []
        if evidence not in existing_evidence:
            merged['retrospective_evidence'] = [*existing_evidence, evidence]
        known[key] = merged
        return False

    first_seen = incoming.get('snapshot_date') or dt.date.today().isoformat()
    known[key] = {
        'brand_id': incoming['brand_id'],
        'brand_name': incoming['brand_name'],
        'product_name': incoming['product_name'],
        'product_url': incoming['product_url'],
        'product_code': incoming['product_code'],
        'display_price': incoming['display_price'],
        'status_labels': incoming['status_labels'],
        'source_url': incoming['source_url'],
        'evidence_level': incoming['evidence_level'],
        'scope_status': COUNTED_SCOPE_STATUS,
        'first_seen_date': first_seen,
        'last_seen_date': first_seen,
        'sales_start_date': None,
        'publication_status': 'PUBLISH_HOLD',
        'human_review_required': True,
        'material_composition': incoming.get('material_composition') or '',
        'function_claims': incoming.get('function_claims') or [],
        'confirmed_design': incoming.get('confirmed_design') or '',
        'season_release': incoming.get('season_release') or '',
        'regular_price_jpy': incoming.get('regular_price_jpy'),
        'sale_price_jpy': incoming.get('sale_price_jpy'),
        'retrospective_months': incoming.get('retrospective_months') or [],
        'retrospective_sources': [incoming['source_path']],
        'retrospective_evidence': [evidence],
        'retrospective_only': True,
    }
    return True


def collect_sources(repo_root: Path):
    data_root = repo_root/'data/brand-md-monitoring'
    sources = []

    manual_path = data_root/'retrospective/manual-products.json'
    if manual_path.exists():
        payload = load_json(manual_path, {})
        for row in payload.get('records', []):
            sources.append((row, str(manual_path.relative_to(repo_root)), payload.get('source_snapshot_date'), True, False))

    spring_path = data_root/'2026-spring-retrospective-baselines.json'
    if spring_path.exists():
        payload = load_json(spring_path, {})
        for row in payload.get('records', []):
            sources.append((row, str(spring_path.relative_to(repo_root)), row.get('backfill_observation_date'), False, True))

    paths = set(data_root.glob('2026-08-*-product-baseline-snapshots.jsonl'))
    paths.update(data_root.glob('2026-08-*-initial-baseline.jsonl'))
    for path in sorted(paths):
        date_match = re.match(r'(2026-08-\d{2})', path.name)
        snapshot = date_match.group(1) if date_match else None
        for row in read_jsonl(path):
            sources.append((row, str(path.relative_to(repo_root)), snapshot, False, False))
    return sources


def active_brand_ids(repo_root: Path):
    payload = load_json(repo_root/'config/brand64-active-brands.json', {})
    active = payload.get('active_brands') or {}
    return set(active) if isinstance(active, dict) else {str(row.get('brand_id')) for row in active if row.get('brand_id')}


def merge_retrospective_sources(root: Path, repo_root: Path | None = None):
    repo_root = repo_root or root.parents[2]
    known_path = root/'known-products.json'
    known = load_json(known_path, {})
    active = active_brand_ids(repo_root)
    source_rows = collect_sources(repo_root)

    accepted = 0
    created = 0
    enriched = 0
    skipped_inactive = 0
    skipped_invalid = 0
    scope_review = 0
    months = {month: 0 for month in sorted(TARGET_MONTHS)}
    unique_keys = set()

    for row, path, snapshot, manual, spring in source_rows:
        normalized = normalize_record(row, path, snapshot, manual=manual, spring=spring)
        if not normalized:
            skipped_invalid += 1
            continue
        if normalized.get('scope_review_only'):
            scope_review += 1
            continue
        if active and normalized['brand_id'] not in active:
            skipped_inactive += 1
            continue
        accepted += 1
        key = normalized['brand_id']+'|'+normalized['product_url']
        unique_keys.add(key)
        for month in normalized.get('retrospective_months', []):
            if month in months:
                months[month] += 1
        if merge_one(known, normalized):
            created += 1
        else:
            enriched += 1

    known_path.write_text(json.dumps(known, ensure_ascii=False, separators=(',', ':'))+'\n')
    summary = {
        'format': 'KC_BRAND64_RETROSPECTIVE_UNIFIED_MERGE',
        'schema_version': '1.0',
        'target_period': '2026-04/2026-09',
        'dedupe_key': 'brand_id|product_url',
        'source_record_count': len(source_rows),
        'accepted_source_record_count': accepted,
        'unique_retrospective_product_key_count': len(unique_keys),
        'created_cumulative_product_count': created,
        'enriched_existing_product_count': enriched,
        'scope_review_only_count': scope_review,
        'skipped_inactive_brand_count': skipped_inactive,
        'skipped_invalid_or_nonofficial_count': skipped_invalid,
        'evidence_counts_by_month': months,
        'cumulative_known_product_count_after_merge': len(known),
        'publication_status': 'PUBLISH_HOLD',
        'human_review_required': True,
        'sales_quantity_estimation': 'FORBIDDEN',
        'first_seen_is_sales_start': False,
    }
    (root/'retrospective-merge-summary.json').write_text(json.dumps(summary, ensure_ascii=False, separators=(',', ':'))+'\n')
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-root', type=Path, default=Path('data/brand-md-monitoring/direct-scans'))
    ap.add_argument('--repo-root', type=Path, default=Path('.'))
    args = ap.parse_args()
    print(json.dumps(merge_retrospective_sources(args.output_root, args.repo_root.resolve()), ensure_ascii=False))


if __name__ == '__main__':
    main()
