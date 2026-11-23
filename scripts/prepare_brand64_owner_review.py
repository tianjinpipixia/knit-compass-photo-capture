#!/usr/bin/env python3
"""Prepare a Git commit for Owner's reviewed cumulative data on this Mac."""
import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlsplit

from publish_brand64_flash_feed import (
    COLLECTOR_CONFIG, PREFIX, add_world_listing_features, attach_world_review,
    git, world_care_reviews,
)
from jun_care_labels import ASSET_ORIGIN, ASSET_ROOT, CARE_FIELDS, REVIEWED_PATHS, REVIEWED_STRIPS, care_observation
from official_care_text import care_from_text, doclasse_feature_labels, named_features


REVIEW_PREFIX = PREFIX + 'owner-reviewed/'
MANIFEST_PATH = 'cumulative-products/manifest.json'
REVIEW_CONFIG = 'config/brand64-world-care-reviews.json'
JUN_REVIEW_CONFIG = 'config/brand64-jun-care-reviews.json'
DOCLASSE_REVIEW_CONFIG = 'config/brand64-doclasse-detail-reviews.json'
DETAIL_SAMPLE_CONFIG = 'config/brand64-reviewed-detail-samples.json'
DOCLASSE_BRAND = 'BR-00018'
# The Owner cumulative browser reader rejects larger responses.
OWNER_SHARD_BYTE_LIMIT = 16_000_000


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def source_file(commit, path):
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'])


def encode(data):
    return (json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n').encode()


def encode_owner_shard(data):
    payload = encode(data)
    if len(payload) > OWNER_SHARD_BYTE_LIMIT:
        # Identity history stays in the canonical shard. The Owner card uses the current record.
        rows = [{name: value for name, value in row.items() if name != 'legacy_identity_records'}
                for row in data['records']]
        payload = encode({**data, 'records': rows})
        if len(payload) > OWNER_SHARD_BYTE_LIMIT:
            raise ValueError(f"Owner shard exceeds the browser limit: {data['brand_id']}")
    return payload


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


def read_jun_reviews(sources, reviewed_on):
    reviews = {}
    for item in json.loads((COLLECTOR_CONFIG.parent/JUN_REVIEW_CONFIG).read_bytes()):
        brand_id, code, url = item['brand_id'], item['product_code'], item['product_url']
        image_url, image_hash = item['image_url'], item['image_sha256']
        brand = sources.get(brand_id, {})
        timestamp = item['retrieved_at_utc']
        at = datetime.fromisoformat(timestamp)
        key = (brand_id, code, url)
        slug = re.escape(brand.get('slug', ''))
        path = rf'/{slug}/product/tops/(?:knit-sweater|cardigan)/{re.escape(code)}'
        if (brand.get('adapter') != 'jun' or not re.fullmatch(r'[A-Z0-9]{6,15}', code)
                or not re.fullmatch(re.escape(ASSET_ORIGIN) + path, url)
                or key in reviews or at.utcoffset() != timedelta(0)
                or not image_url.startswith(ASSET_ORIGIN + ASSET_ROOT)
                or image_url[len(ASSET_ORIGIN):] not in REVIEWED_PATHS
                or image_hash not in REVIEWED_STRIPS):
            raise ValueError(f'Invalid reviewed JUN care record for {code}')
        label = {
            **dict(zip(CARE_FIELDS, REVIEWED_STRIPS[image_hash])),
            'status': 'verified', 'image_url': image_url, 'image_sha256': image_hash,
        }
        care = care_observation({'care_label': label, 'source_url': url,
                                 'source_sha256': item['source_sha256'], 'retrieved_at_utc': timestamp})
        if care is None:
            raise ValueError(f'Unverified JUN care record for {code}')
        if at.astimezone(timezone(timedelta(hours=9))).date().isoformat() <= reviewed_on:
            reviews[key] = care
    return reviews


def read_doclasse_reviews(sources, reviewed_on):
    reviews = {}
    if sources.get(DOCLASSE_BRAND, {}).get('adapter') != 'doclasse':
        raise ValueError('DoCLASSE review source does not match the brand registry')
    for item in json.loads((COLLECTOR_CONFIG.parent/DOCLASSE_REVIEW_CONFIG).read_bytes()):
        code, url = item['product_code'], item['product_url']
        key = (DOCLASSE_BRAND, code, url)
        timestamp, digest = item['retrieved_at_utc'], item['source_sha256']
        at = datetime.fromisoformat(timestamp)
        path = r'https://www\.doclasse\.com/item/detail/1_1_'+re.escape(code)+r'(?:/[0-9]+)?'
        claims = item.get('function_source_text', {})
        if (not re.fullmatch(r'[0-9]{5,8}', code) or not re.fullmatch(path, url)
                or key in reviews or at.utcoffset() != timedelta(0)
                or not re.fullmatch(r'[a-f0-9]{64}', digest)
                or not isinstance(claims, dict)
                or any(not isinstance(text, str) or claim not in doclasse_feature_labels(text)
                       for claim, text in claims.items())):
            raise ValueError(f'Invalid reviewed DoCLASSE detail for {code}')
        care = care_from_text(item.get('care_text'))
        if not care or care['status'] != 'verified':
            care = None
        if not care and not claims:
            raise ValueError(f'No confirmed care or function evidence for {code}')
        if at.astimezone(timezone(timedelta(hours=9))).date().isoformat() <= reviewed_on:
            evidence = {'source_url': url, 'source_sha256': digest, 'retrieved_at_utc': timestamp}
            reviews[key] = (care and {**care, **evidence}, claims, evidence)
    return reviews


def read_detail_samples(sources, reviewed_on):
    samples = {}
    for item in json.loads((COLLECTOR_CONFIG.parent/DETAIL_SAMPLE_CONFIG).read_bytes()):
        brand_id, code, url = item['brand_id'], item['product_code'], item['product_url']
        key = (brand_id, code, url)
        brand = sources.get(brand_id, {})
        official_hosts = {urlsplit(entry).hostname for entry in
                          brand.get('entry_urls', []) + brand.get('watch_product_urls', [])}
        product = urlsplit(url)
        timestamp, digest = item['retrieved_at_utc'], item['source_sha256']
        at = datetime.fromisoformat(timestamp)
        claims = item.get('function_source_text', {})
        composition = item.get('composition')
        if (product.scheme != 'https' or product.netloc not in official_hosts or product.fragment
                or not re.fullmatch(r'[A-Za-z0-9-]{3,32}', code) or key in samples
                or at.utcoffset() != timedelta(0) or not re.fullmatch(r'[a-f0-9]{64}', digest)
                or not isinstance(claims, dict)
                or any(not isinstance(label, str) or claim not in named_features([label])
                       for claim, label in claims.items())
                or (composition is not None and (brand.get('adapter') != 'jun'
                    or not isinstance(composition, str) or not re.search(r'\d\s*%', composition)))):
            raise ValueError(f'Invalid reviewed product detail for {code}')
        evidence = {'source_url': url, 'source_sha256': digest, 'retrieved_at_utc': timestamp}
        care = None
        if 'care_label' in item:
            care = care_observation({**evidence, 'care_label': item['care_label']})
            if not care or care['status'] != 'verified':
                raise ValueError(f'Unverified product care for {code}')
        if not care and not claims and not composition:
            raise ValueError(f'No confirmed product detail for {code}')
        if at.astimezone(timezone(timedelta(hours=9))).date().isoformat() <= reviewed_on:
            samples[key] = (care, claims, evidence, composition)
    return samples


def apply_reviewed_detail(record, review):
    care, claims, evidence = review
    saved_care = record.get('care_label') or {}
    fields = ('home_wash', 'dry_clean')
    if (care and all(saved_care.get(field) in (None, 'unknown', care.get(field)) for field in fields)
            and any(saved_care.get(field) in (None, 'unknown') and care[field] != 'unknown' for field in fields)):
        record['care_label'] = care
    saved_claims = record.get('function_claims') or []
    new_claims = {claim: label for claim, label in claims.items() if claim not in saved_claims}
    if new_claims:
        record['function_claims'] = [*saved_claims, *new_claims]
        record['function_review_evidence'] = {**evidence, 'claim_text': new_claims}


def apply_detail_sample(record, sample):
    care, claims, evidence, composition = sample
    apply_reviewed_detail(record, (care, claims, evidence))
    if composition and not (record.get('material_composition') or '').strip():
        record['material_composition'] = composition
        record['composition_detail_evidence'] = evidence


def prepare(base_ref, reviewed_on, previous_ref):
    collector = checked_commit('HEAD')
    top = Path(git('rev-parse', '--show-toplevel').stdout.strip())
    if top != COLLECTOR_CONFIG.parent:
        raise ValueError('Run this command from the collector checkout')
    for file in (REVIEW_CONFIG, JUN_REVIEW_CONFIG, DOCLASSE_REVIEW_CONFIG, DETAIL_SAMPLE_CONFIG,
                 'config/brand64-free-direct-sources.json'):
        if (top/file).read_bytes() != source_file(collector, file):
            raise ValueError(f'{file} must match the committed review source')
    base_commit, digest, day, run_id, brands = read_base(checked_commit(base_ref))
    if reviewed_on < day:
        raise ValueError('The review date must be on or after the canonical observation date')
    sources = json.loads((COLLECTOR_CONFIG/'brand64-free-direct-sources.json').read_bytes())['brands']
    reviews = world_care_reviews(sources)
    jun_reviews = read_jun_reviews(sources, reviewed_on)
    doclasse_reviews = read_doclasse_reviews(sources, reviewed_on)
    detail_samples = read_detail_samples(sources, reviewed_on)
    review_brands = {brand_id for brand_id, _, _ in (*reviews, *jun_reviews, *doclasse_reviews, *detail_samples)}
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
            key = (brand_id, row.get('product_code'), row['product_url'])
            care = jun_reviews.get(key)
            if care and (row.get('care_label') or {}).get('status') != 'verified':
                row['care_label'] = care
            if key in doclasse_reviews:
                apply_reviewed_detail(row, doclasse_reviews[key])
            if key in detail_samples:
                apply_detail_sample(row, detail_samples[key])
            changed += before != row
            care = row.get('care_label') or {}
            missing += (care.get('status') != 'verified' or any(
                care.get(key) in (None, 'unknown') for key in ('home_wash', 'dry_clean')))
        report[brand_id] = {'products': len(records), 'changed': changed, 'care_unconfirmed': missing}
        if changed or len(raw) > OWNER_SHARD_BYTE_LIMIT:
            files[name] = encode_owner_shard(data)
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
