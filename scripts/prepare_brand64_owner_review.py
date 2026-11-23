#!/usr/bin/env python3
"""Prepare a Git commit for Owner's reviewed cumulative data on this Mac."""
import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from publish_brand64_flash_feed import (
    COLLECTOR_CONFIG, PREFIX, add_world_listing_features, attach_world_review,
    git, world_care_reviews,
)


REVIEW_PREFIX = PREFIX + 'owner-reviewed/'
MANIFEST_PATH = 'cumulative-products/manifest.json'
REVIEW_CONFIG = 'config/brand64-world-care-reviews.json'


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def source_file(commit, path):
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'])


def encode(data):
    return (json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n').encode()


def checked_commit(ref):
    return git('rev-parse', '--verify', '--end-of-options', ref+'^{commit}').stdout.strip()


def read_base(head):
    read = lambda commit, name: source_file(commit, PREFIX + name)
    binding = json.loads(read(head, 'snapshot-binding.json'))
    index = json.loads(read(head, 'md-baseline-index.json'))
    day = binding['observation_date']
    anchor = next(row for row in index['entries'] if row['observation_date'] == day)
    commit = anchor['bound_commit']
    digest = binding['canonical_manifest_sha256']
    run_id = str(binding['collection_run_id'])
    if (not re.fullmatch(r'[0-9a-f]{40}', commit)
            or date.fromisoformat(day).isoformat() != day
            or binding['format'] != 'KC_BRAND64_DAILY_PIPELINE_SNAPSHOT'
            or binding['canonical_status'] != 'VALIDATED'
            or binding['analysis_ready'] is not True
            or binding['publication_status'] != 'PUBLISH_HOLD'
            or binding['human_review_required'] is not True
            or index['format'] != 'KC_BRAND64_MD_BASELINE_INDEX'
            or index['branch'] != 'brand64/flash-feed'
            or index['anchor_observation_date'] != day
            or not run_id.isdigit() or str(anchor['collection_run_id']) != run_id
            or anchor['canonical_manifest_sha256'] != digest
            or json.loads(read(commit, 'snapshot-binding.json')) != binding):
        raise ValueError('The current canonical observation binding and index disagree')
    raw = read(commit, MANIFEST_PATH)
    manifest = json.loads(raw)
    if (checksum(raw) != digest or manifest['observation_date'] != day
            or manifest['format'] != 'KC_BRAND64_CUMULATIVE_PRODUCTS_INDEX'
            or manifest['publication_status'] != 'PUBLISH_HOLD'
            or manifest['human_review_required'] is not True
            or manifest['formal_product_registration'] is not False):
        raise ValueError('The immutable canonical cumulative manifest failed validation')
    return commit, digest, day, run_id, manifest['brands']


def create_commit(files, message, parent=None):
    # An isolated index keeps working files and all other refs intact.
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        env = {**os.environ, 'GIT_INDEX_FILE': str(temp/'index')}
        git('read-tree', '--empty', env=env)
        for name, data in files.items():
            (temp/'payload').write_bytes(data)
            blob = git('hash-object', '-w', str(temp/'payload')).stdout.strip()
            git('update-index', '--add', '--cacheinfo', '100644', blob, REVIEW_PREFIX+name, env=env)
        tree = git('write-tree', env=env).stdout.strip()
        parents = ['-p', parent] if parent else []
        return git('commit-tree', tree, *parents, input=message+'\n', env=env).stdout.strip()


def prepare(base_ref, reviewed_on, previous_ref):
    collector = checked_commit('HEAD')
    top = Path(git('rev-parse', '--show-toplevel').stdout.strip())
    if top != COLLECTOR_CONFIG.parent:
        raise ValueError('Run this command from the collector checkout')
    for file in (REVIEW_CONFIG, 'config/brand64-free-direct-sources.json'):
        if (top/file).read_bytes() != source_file(collector, file):
            raise ValueError(f'{file} must match the committed review source')
    base_commit, digest, day, run_id, brands = read_base(checked_commit(base_ref))
    if reviewed_on < day:
        raise ValueError('The review date must be on or after the canonical observation date')
    sources = json.loads((COLLECTOR_CONFIG/'brand64-free-direct-sources.json').read_bytes())['brands']
    reviews = world_care_reviews(sources)
    review_brands = {brand_id for brand_id, _, _ in reviews}
    files, descriptors, report = {}, {}, {}
    for brand in brands:
        brand_id = brand['brand_id']
        if brand_id not in review_brands:
            continue
        name = f'{brand_id}.json'
        path = 'cumulative-products/' + name
        if not re.fullmatch(r'BR-[0-9]{5}', brand_id) or brand['path'] != path or brand_id in report:
            raise ValueError(f'Invalid or duplicate canonical brand descriptor: {brand_id}')
        raw = source_file(base_commit, PREFIX+path)
        data = json.loads(raw)
        records = data['records']
        if (checksum(raw) != brand['sha256'] or data['brand_id'] != brand_id
                or data['observation_date'] != day or data['brand_name'] != brand['brand_name']
                or data['format'] != 'KC_BRAND64_CUMULATIVE_PRODUCTS_BRAND'
                or data['publication_status'] != 'PUBLISH_HOLD'
                or data['human_review_required'] is not True
                or data['formal_product_registration'] is not False
                or len(records) != brand['product_count'] or data['product_count'] != len(records)
                or len({row['product_url'] for row in records}) != len(records)
                or any(row['brand_id'] != brand_id or row['brand_name'] != data['brand_name'] for row in records)):
            raise ValueError(f'Invalid canonical shard: {brand_id}')
        changed = missing = 0
        for row in records:
            before = row.copy()
            add_world_listing_features(row, sources[brand_id])
            attach_world_review(row, reviews, reviewed_on, same_day=False)
            changed += before != row
            care = row.get('care_label') or {}
            missing += (care.get('status') != 'verified' or any(
                care.get(key) in (None, 'unknown') for key in ('home_wash', 'dry_clean')))
        report[brand_id] = {'products': len(records), 'changed': changed, 'care_unconfirmed': missing}
        if changed:
            files[name] = encode(data)
            descriptors[brand_id] = {'sha256': checksum(files[name]), 'base_sha256': brand['sha256']}
    previous = checked_commit(previous_ref) if previous_ref else None
    data_commit = create_commit(files, 'Save locally reviewed Brand64 cumulative shards [skip ci]', previous)
    pointer = {
        'format': 'KC_BRAND64_OWNER_REVIEWED_SUPPLEMENT', 'schema_version': '1.0',
        'publication_status': 'PUBLISH_HOLD', 'human_review_required': True,
        'formal_product_registration': False, 'reviewed_on': reviewed_on,
        'observation_date': day, 'collection_run_id': run_id,
        'base_commit': base_commit, 'base_manifest_sha256': digest,
        'collector_commit': collector, 'data_commit': data_commit, 'brands': descriptors,
    }
    commit = create_commit({'manifest.json': encode(pointer)},
                           'Point Owner to reviewed Brand64 cumulative data [skip ci]', data_commit)
    return {**pointer, 'ref': 'refs/heads/brand64/owner-reviewed', 'commit': commit, 'coverage': report}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ref', required=True, help='Fetched canonical brand64/flash-feed head')
    parser.add_argument('--reviewed-on', type=date.fromisoformat, required=True, help='Review date in JST')
    parser.add_argument('--previous-ref', help='Fetched current brand64/owner-reviewed head, if present')
    args = parser.parse_args()
    result = prepare(args.base_ref, args.reviewed_on.isoformat(), args.previous_ref)
    print(json.dumps(result, ensure_ascii=False, indent=2))
