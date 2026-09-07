#!/usr/bin/env python3
"""Atomically publish the read-only owner feed and restart state to one Git branch."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from brand64_flash_pipeline import STATE_FILES

BRANCH = 'brand64/flash-feed'
PREFIX = 'data/brand-md-monitoring/direct-scans/'
OBSERVED_DIR = 'observed-products'
COUNTED_SCOPE_STATUS = 'BRAND_AND_KNIT_PATH_MATCHED'


def git(*args, env=None, input=None, check=True):
    return subprocess.run(['git', *args], check=check, text=True, input=input,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)


def build_observed_product_shards(root):
    """Build compact per-brand observation files without promoting them to formal products.

    The exported rows must use exactly the same counting boundary as
    brand64_flash_pipeline.build_summary(): current observation date only and
    scope_status == BRAND_AND_KNIT_PATH_MATCHED. Link candidates and stale rows
    stay in durable recovery/history state but are not part of the displayed MD
    observation count.
    """
    coverage = json.loads((root/'coverage-state.json').read_text())
    latest = json.loads((root/'latest.json').read_text())
    observed_date = latest.get('observed_date') or latest.get('observation_date')
    if not observed_date:
        raise ValueError('latest.json has no observation date')

    output = root/OBSERVED_DIR
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    manifest_brands = []
    generated = []
    product_count = 0
    for brand_id in sorted(coverage):
        state = coverage[brand_id]
        if state.get('observed_date') != observed_date:
            continue
        items = [
            item for item in (state.get('surface_items') or [])
            if item.get('scope_status') == COUNTED_SCOPE_STATUS
        ]
        if not items:
            continue
        brand_name = state.get('brand_name') or brand_id
        records = []
        for item in items:
            records.append({
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
                'observed_date': observed_date,
            })
        file_name = f'{brand_id}.json'
        relative = f'{OBSERVED_DIR}/{file_name}'
        payload = {
            'format': 'KC_BRAND64_OBSERVED_PRODUCTS_BRAND',
            'schema_version': '1.0',
            'observation_date': observed_date,
            'brand_id': brand_id,
            'brand_name': brand_name,
            'product_count': len(records),
            'publication_status': 'PUBLISH_HOLD',
            'human_review_required': True,
            'formal_product_registration': False,
            'records': records,
        }
        (output/file_name).write_text(
            json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n'
        )
        generated.append(relative)
        manifest_brands.append({
            'brand_id': brand_id,
            'brand_name': brand_name,
            'product_count': len(records),
            'path': relative,
        })
        product_count += len(records)

    expected_products = int(latest.get('product_count') or 0)
    expected_brands = int(latest.get('product_observed_brand_count') or 0)
    if product_count != expected_products:
        raise ValueError(f'Observed product export mismatch: {product_count} != {expected_products}')
    if len(manifest_brands) != expected_brands:
        raise ValueError(f'Observed brand export mismatch: {len(manifest_brands)} != {expected_brands}')

    manifest = {
        'format': 'KC_BRAND64_OBSERVED_PRODUCTS_INDEX',
        'schema_version': '1.0',
        'observation_date': observed_date,
        'active_brand_count': int(latest.get('active_brand_count') or 0),
        'attempted_brand_count': int(latest.get('attempted_brand_count') or 0),
        'product_observed_brand_count': expected_brands,
        'observed_product_count': expected_products,
        'coverage_status': latest.get('scan_status') or 'UNKNOWN',
        'publication_status': 'PUBLISH_HOLD',
        'human_review_required': True,
        'formal_product_registration': False,
        'sales_quantity_estimation': 'FORBIDDEN',
        'first_seen_is_sales_start': False,
        'brands': manifest_brands,
    }
    manifest_relative = f'{OBSERVED_DIR}/manifest.json'
    (output/'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))+'\n'
    )
    return [manifest_relative, *generated]


def publish(root):
    generated = build_observed_product_shards(root)
    names = [*STATE_FILES, 'feed.json', 'latest.json', 'flash-latest.json', 'summary.md', *generated]
    for name in names:
        if not (root/name).is_file(): raise ValueError('Missing checkpoint: '+name)
    with tempfile.TemporaryDirectory() as directory:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(directory)/'index')}
        # Never force-push: if another run advanced the feed, leave the conflict visible.
        existing = git('ls-remote', '--heads', 'origin', 'refs/heads/'+BRANCH).stdout.strip()
        parent = None
        if existing:
            git('fetch', '--depth=1', 'origin', BRANCH)
            parent = git('rev-parse', 'FETCH_HEAD').stdout.strip()
        git('read-tree', '--empty', env=env)
        for name in names:
            blob = git('hash-object', '-w', str(root/name)).stdout.strip()
            git('update-index', '--add', '--cacheinfo', '100644', blob, PREFIX+name, env=env)
        tree = git('write-tree', env=env).stdout.strip()
        args = ['commit-tree', tree]
        if parent: args += ['-p', parent]
        commit = git(*args, input='Update daily owner flash, recovery state and observed product index\n').stdout.strip()
        git('push', 'origin', commit+':refs/heads/'+BRANCH)
        print('Published owner flash, recovery state and observed product index: '+commit)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-root', type=Path, default=Path('data/brand-md-monitoring/direct-scans'))
    publish(ap.parse_args().output_root)
