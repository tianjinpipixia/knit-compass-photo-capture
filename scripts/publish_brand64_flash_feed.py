#!/usr/bin/env python3
"""Atomically publish the read-only owner feed and restart state to one Git branch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from brand64_canonical_store import CANONICAL, normalize_identities, read_pool, seed_working_state, attach_details
from brand64_flash_pipeline import STATE_FILES
from merge_brand64_retrospective_sources import merge_retrospective_sources
from brand64_identity_guard import persist_reconciled

BRANCH = 'brand64/flash-feed'
PREFIX = 'data/brand-md-monitoring/direct-scans/'
OBSERVED_DIR = 'observed-products'
CUMULATIVE_DIR = 'cumulative-products'
COUNTED_SCOPE_STATUS = 'BRAND_AND_KNIT_PATH_MATCHED'


def git(*args, env=None, input=None, check=True):
    return subprocess.run(['git', *args], check=check, text=True, input=input,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)


def compact_record(brand_id, brand_name, item, observed_date=None):
    return {
        **item,
        'brand_id': brand_id,
        'brand_name': brand_name,
        'product_name': item.get('product_name') or '',
        'product_url': item.get('product_url') or '',
        'product_code': item.get('product_code') or '',
        'display_price': item.get('display_price') or '',
        'status_labels': item.get('status_labels') or [],
        'source_url': item.get('source_url') or '',
        'evidence_level': item.get('evidence_level') or '',
        'scope_status': item.get('scope_status') or '',
        'observed_date': observed_date or item.get('last_seen_date') or '',
        'first_seen_date': item.get('first_seen_date'),
        'last_seen_date': item.get('last_seen_date'),
        'material_composition': item.get('material_composition') or '',
        'function_claims': item.get('function_claims') or [],
        'confirmed_design': item.get('confirmed_design') or '',
        'season_release': item.get('season_release') or '',
        'regular_price_jpy': item.get('regular_price_jpy'),
        'sale_price_jpy': item.get('sale_price_jpy'),
        'retrospective_months': item.get('retrospective_months') or [],
        'retrospective_sources': item.get('retrospective_sources') or [],
        'retrospective_only': bool(item.get('retrospective_only')),
    }


def write_brand_shard(output, directory, brand_id, brand_name, records, observation_date, cumulative=False):
    file_name = f'{brand_id}.json'
    relative = f'{directory}/{file_name}'
    payload = {
        'format': 'KC_BRAND64_CUMULATIVE_PRODUCTS_BRAND' if cumulative else 'KC_BRAND64_OBSERVED_PRODUCTS_BRAND',
        'schema_version': '1.1' if cumulative else '1.0',
        'observation_date': observation_date,
        'brand_id': brand_id,
        'brand_name': brand_name,
        'product_count': len(records),
        'publication_status': 'PUBLISH_HOLD',
        'human_review_required': True,
        'formal_product_registration': False,
        'records': records,
    }
    (output/file_name).write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n')
    return relative


def build_observed_product_shards(root):
    coverage = json.loads((root/'coverage-state.json').read_text())
    latest = json.loads((root/'latest.json').read_text())
    observed_date = latest.get('observed_date') or latest.get('observation_date')
    if not observed_date:
        raise ValueError('latest.json has no observation date')
    output = root/OBSERVED_DIR
    output.mkdir(parents=True, exist_ok=True)
    manifest_brands = []
    generated = []
    product_count = 0
    for brand_id in sorted(coverage):
        state = coverage[brand_id]
        if state.get('observed_date') != observed_date:
            continue
        items = [item for item in (state.get('surface_items') or []) if item.get('scope_status') == COUNTED_SCOPE_STATUS]
        if not items:
            continue
        brand_name = state.get('brand_name') or brand_id
        records = [compact_record(brand_id, brand_name, item, observed_date) for item in items]
        relative = write_brand_shard(output, OBSERVED_DIR, brand_id, brand_name, records, observed_date)
        generated.append(relative)
        manifest_brands.append({'brand_id': brand_id, 'brand_name': brand_name, 'product_count': len(records), 'path': relative})
        product_count += len(records)
    expected_products = int(latest.get('product_count') or 0)
    expected_brands = int(latest.get('product_observed_brand_count') or 0)
    if product_count != expected_products:
        raise ValueError(f'Observed product export mismatch: {product_count} != {expected_products}')
    if len(manifest_brands) != expected_brands:
        raise ValueError(f'Observed brand export mismatch: {len(manifest_brands)} != {expected_brands}')
    manifest = {
        'format': 'KC_BRAND64_OBSERVED_PRODUCTS_INDEX', 'schema_version': '1.0',
        'observation_date': observed_date,
        'active_brand_count': int(latest.get('active_brand_count') or 0),
        'attempted_brand_count': int(latest.get('attempted_brand_count') or 0),
        'product_observed_brand_count': expected_brands,
        'observed_product_count': expected_products,
        'coverage_status': latest.get('scan_status') or 'UNKNOWN',
        'publication_status': 'PUBLISH_HOLD', 'human_review_required': True,
        'formal_product_registration': False, 'sales_quantity_estimation': 'FORBIDDEN',
        'first_seen_is_sales_start': False, 'brands': manifest_brands,
    }
    manifest_relative = f'{OBSERVED_DIR}/manifest.json'
    (output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))+'\n')
    return [manifest_relative, *generated]


def build_cumulative_product_shards(root, active=None):
    previous = read_pool(root) or {}
    known = seed_working_state(root)
    review = []
    if active is not None:
        known, review = persist_reconciled(root, known, active)
    details_path = root/'detail-results.json'
    attach_details(known, json.loads(details_path.read_text()) if details_path.exists() else {})
    latest = json.loads((root/'latest.json').read_text())
    observation_date = latest.get('observed_date') or latest.get('observation_date')
    if not observation_date:
        raise ValueError('latest.json has no observation date')
    output = root/CUMULATIVE_DIR
    output.mkdir(parents=True, exist_ok=True)
    grouped = {}
    for record in known.values():
        if not isinstance(record, dict):
            continue
        brand_id = record.get('brand_id') or ''
        product_url = record.get('product_url') or ''
        if not brand_id or not product_url or record.get('scope_status') != COUNTED_SCOPE_STATUS:
            continue
        grouped.setdefault(brand_id, {})[product_url] = record
    manifest_brands = []
    generated = []
    cumulative_count = 0
    retrospective_product_count = 0
    months = {f'2026-{month:02d}': 0 for month in range(4, 10)}
    earliest_first_seen = None
    for brand_id in sorted(grouped):
        by_url = grouped[brand_id]
        records = []
        brand_name = brand_id
        for product_url in sorted(by_url):
            item = by_url[product_url]
            brand_name = item.get('brand_name') or brand_name
            first_seen = item.get('first_seen_date')
            if first_seen and (earliest_first_seen is None or first_seen < earliest_first_seen):
                earliest_first_seen = first_seen
            retrospective_months = item.get('retrospective_months') or []
            if retrospective_months:
                retrospective_product_count += 1
                for month in retrospective_months:
                    if month in months:
                        months[month] += 1
            records.append(compact_record(brand_id, brand_name, item))
        relative = write_brand_shard(output, CUMULATIVE_DIR, brand_id, brand_name, records, observation_date, cumulative=True)
        generated.append(relative)
        manifest_brands.append({'brand_id': brand_id, 'brand_name': brand_name, 'product_count': len(records), 'path': relative, 'sha256': hashlib.sha256((root/relative).read_bytes()).hexdigest()})
        cumulative_count += len(records)
    manifest = {
        'format': 'KC_BRAND64_CUMULATIVE_PRODUCTS_INDEX', 'schema_version': '1.2',
        'canonical_source': CANONICAL,
        'observation_date': observation_date,
        'cumulative_from_date': earliest_first_seen,
        'active_brand_count': int(latest.get('active_brand_count') or 0),
        'attempted_brand_count_today': int(latest.get('attempted_brand_count') or 0),
        'product_observed_brand_count_today': int(latest.get('product_observed_brand_count') or 0),
        'observed_product_count_today': int(latest.get('product_count') or 0),
        'cumulative_product_brand_count': len(manifest_brands),
        'cumulative_unique_product_count': cumulative_count,
        'retrospective_product_count': retrospective_product_count,
        'retrospective_evidence_counts_by_month': months,
        'retrospective_target_period': '2026-04/2026-09',
        'dedupe_key': 'brand_id|product_url',
        'publication_status': 'PUBLISH_HOLD', 'human_review_required': True,
        'formal_product_registration': False, 'sales_quantity_estimation': 'FORBIDDEN',
        'first_seen_is_sales_start': False, 'brands': manifest_brands,
    }
    identity_review = {r['identity_key']: r for r in review if r.get('reason') == 'BRAND_IDENTITY_CONFLICT'}
    manifest['identity_review_product_count'] = len(identity_review)
    catalogue = {**manifest, 'format': 'KC_BRAND64_CANONICAL_CATALOGUE',
                 'records': [compact_record(bid, grouped[bid][url].get('brand_name') or bid, grouped[bid][url])
                             for bid in sorted(grouped) for url in sorted(grouped[bid])],
                 'daily_summary': latest}
    feed_path = root/'feed.json'
    daily_feed = json.loads(feed_path.read_text()) if feed_path.exists() else {}
    catalogue['daily_events'] = [
        {field: event.get(field) for field in ('brand_id', 'product_url', 'observed_date', 'delta_type', 'previous_values', 'is_new_release_confirmed')}
        for event in daily_feed.get('candidates', [])]
    catalogue_path = output/'catalogue.json'
    catalogue_path.write_text(json.dumps(catalogue, ensure_ascii=False, separators=(',', ':'))+'\n')
    generated.append(f'{CUMULATIVE_DIR}/catalogue.json')
    manifest['catalogue'] = {'path': f'{CUMULATIVE_DIR}/catalogue.json',
                             'sha256': hashlib.sha256(catalogue_path.read_bytes()).hexdigest(),
                             'product_count': cumulative_count}
    manifest_relative = f'{CUMULATIVE_DIR}/manifest.json'
    (output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))+'\n')
    exported = read_pool(root)
    for key, row in normalize_identities(previous).items():
        if key not in exported and not any(r.get('identity_key') == key and r.get('record') == row
                                           for r in review if r.get('reason') == 'BRAND_IDENTITY_CONFLICT'):
            raise ValueError('Refusing canonical product loss without exact retained review evidence')
    return [manifest_relative, *generated]


def publish(root):
    repo_root = Path.cwd().resolve()
    # Pin the parent before reading and building. A concurrent publication makes
    # the final non-force push fail instead of overwriting its products.
    existing = git('ls-remote', '--heads', 'origin', 'refs/heads/'+BRANCH).stdout.strip()
    parent = None
    if existing:
        git('fetch', '--depth=1', 'origin', BRANCH)
        parent = git('rev-parse', 'FETCH_HEAD').stdout.strip()
        paths = git('ls-tree', '-r', '--name-only', parent, '--', PREFIX+CUMULATIVE_DIR).stdout.splitlines()
        for path in paths:
            relative = Path(path).relative_to(PREFIX)
            target = root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(git('show', parent+':'+path).stdout, encoding='utf-8')
    seed_working_state(root)
    retro_dir = repo_root/'data/brand-md-monitoring/retrospective'
    expected_manual_files = list(retro_dir.glob('manual*.json')) if retro_dir.exists() else []
    merge_summary = merge_retrospective_sources(root, repo_root)
    if expected_manual_files and int(merge_summary.get('source_record_count') or 0) == 0:
        raise ValueError(f'Retrospective files exist ({len(expected_manual_files)}) but source_record_count is 0')
    print('Retrospective source records:', merge_summary.get('source_record_count'), 'months:', merge_summary.get('evidence_counts_by_month'))
    current_generated = build_observed_product_shards(root)
    active = json.loads((repo_root/'config/brand64-active-brands.json').read_text())['active_brands']
    cumulative_generated = build_cumulative_product_shards(root, active)
    generated = [*current_generated, *cumulative_generated, 'cumulative-products/review-queue.json']
    names = [*STATE_FILES, 'feed.json', 'latest.json', 'flash-latest.json', 'summary.md', 'retrospective-merge-summary.json', *generated]
    for name in names:
        if not (root/name).is_file(): raise ValueError('Missing checkpoint: '+name)
    with tempfile.TemporaryDirectory() as directory:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(directory)/'index')}
        git('read-tree', parent if parent else '--empty', env=env)
        for name in names:
            blob = git('hash-object', '-w', str(root/name)).stdout.strip()
            git('update-index', '--add', '--cacheinfo', '100644', blob, PREFIX+name, env=env)
        tree = git('write-tree', env=env).stdout.strip()
        args = ['commit-tree', tree]
        if parent: args += ['-p', parent]
        commit = git(*args, input='Update unified daily and retrospective Brand64 product pool\n').stdout.strip()
        git('push', 'origin', commit+':refs/heads/'+BRANCH)
        print('Published unified daily and retrospective Brand64 product pool: '+commit)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-root', type=Path, default=Path('data/brand-md-monitoring/direct-scans'))
    publish(ap.parse_args().output_root)
