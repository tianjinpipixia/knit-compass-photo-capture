#!/usr/bin/env python3
"""Atomically publish the read-only owner feed and restart state to one Git branch."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from brand64_canonical_store import CANONICAL, normalize_identities, read_pool, seed_working_state, attach_details
from brand64_flash_pipeline import STATE_FILES
from merge_brand64_retrospective_sources import merge_retrospective_sources
from brand64_identity_guard import persist_reconciled
from jun_care_labels import care_observation
from official_care_text import CARE_TEXT_SOURCE, add_world_listing_features, jis_care_text, named_features
from brand64_history_store import history_files, write_history, read_history, DIRECTORY as HISTORY_DIRECTORY
from brand64_canonical_chunks import add_canonical_chunks

BRANCH = 'brand64/flash-feed'
PREFIX = 'data/brand-md-monitoring/direct-scans/'
OBSERVED_DIR = 'observed-products'
CUMULATIVE_DIR = 'cumulative-products'
COLLECTOR_CONFIG = Path(__file__).resolve().parents[1]/'config'
OBSERVED_COUNTED_SCOPE_STATUS = 'BRAND_AND_KNIT_PATH_MATCHED'
CUMULATIVE_COUNTED_SCOPE_STATUSES = {
    OBSERVED_COUNTED_SCOPE_STATUS,
    'OFFICIAL_REGULAR_LINE_WOMENS_KNIT_CONFIRMED',
}


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


def world_care_reviews(sources):
    """Load item-level results reviewed from saved first-party browser snapshots."""
    reviewed = {}
    for item in json.loads((COLLECTOR_CONFIG/'brand64-world-care-reviews.json').read_text()):
        brand = sources.get(item['brand_id'], {})
        code = item['product_code']
        url = item['product_url']
        key = (item['brand_id'], code, url)
        image_url = item['image_url']
        material = item.get('material_composition')
        tags = item.get('related_function_tags', {})
        at = datetime.fromisoformat(item['retrieved_at_utc'].replace('Z', '+00:00'))
        care = jis_care_text(item['jis_symbols'], 'world_browser_symbols')
        if (brand.get('adapter') != 'world' or not re.fullmatch(r'[A-Z0-9]{10,22}', code)
                or url != f"https://store.world.co.jp/brand/{brand['slug']}/item/{code}"
                or not re.fullmatch(r'https://store\.world\.co\.jp/res/c/wash/sp/wash[0-9]{1,5}\.png\?ver=2', image_url)
                or item['image_media_type'] not in {'image/avif', 'image/png', 'image/webp'}
                or at.utcoffset() != timedelta(0) or key in reviewed
                or not all(re.fullmatch(r'[0-9a-f]{64}', item[field])
                           for field in ('source_sha256', 'image_sha256', 'snapshot_sha256'))
                or ('material_composition' in item and (not isinstance(material, str) or not material.strip()))
                or not care or 'unknown' in (care['home_wash'], care['dry_clean'])):
            raise ValueError(f'Invalid reviewed WORLD care record for {code}')
        if not isinstance(tags, dict) or any(
            not named_features([label]) or not isinstance(link, str)
            or not re.fullmatch(r'https://store\.world\.co\.jp/search\?ta=[A-Z0-9]{2,12}', link)
            for label, link in tags.items()
        ):
            raise ValueError(f'Invalid reviewed WORLD function tags for {code}')
        care.pop('source_text')
        care.update(evidence_kind='official_browser_image', source_url=url, image_url=image_url,
                    retrieved_at_utc=at.isoformat(), source_sha256=item['source_sha256'],
                    image_sha256=item['image_sha256'], snapshot_sha256=item['snapshot_sha256'],
                    image_media_type=item['image_media_type'])
        reviewed[key] = (at, care, material, tags)
    return reviewed


def attach_world_review(record, reviews, observation_date, *, same_day):
    reviewed = reviews.get((record.get('brand_id'), record.get('product_code'), record.get('product_url')))
    if reviewed is None:
        return
    at, care, material, tags = reviewed
    day = at.astimezone(timezone(timedelta(hours=9))).date().isoformat()
    if day > observation_date or (same_day and day != observation_date):
        return
    if material and not record.get('material_composition'):
        record['material_composition'] = material
        record['composition_detail_evidence'] = {
            key: care[key] for key in ('source_url', 'source_sha256', 'retrieved_at_utc')
        }
    if tags:
        claims = named_features(tags)
        record['function_claims'] = list(dict.fromkeys([*(record.get('function_claims') or []), *claims]))
        record['function_browser_evidence'] = {
            **{key: care[key] for key in ('source_url', 'source_sha256', 'retrieved_at_utc')},
            'claim_text': claims,
            'tag_urls': tags,
        }
    previous = record.get('care_label')
    if (isinstance(previous, dict) and previous.get('status') == 'verified'
            and previous.get('source_url') == record['product_url']):
        try:
            last = datetime.fromisoformat(str(previous.get('retrieved_at_utc') or '').replace('Z', '+00:00'))
            if last.tzinfo is not None and last >= at:
                return
        except ValueError:
            pass
    record['care_label'] = care


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
    sources = json.loads((COLLECTOR_CONFIG/'brand64-free-direct-sources.json').read_text())['brands']
    world_reviews = world_care_reviews(sources)
    details_path = root/'detail-results.json'
    saved_details = json.loads(details_path.read_text()) if details_path.exists() else {}
    output = root/OBSERVED_DIR
    output.mkdir(parents=True, exist_ok=True)
    manifest_brands = []
    generated = []
    product_count = 0
    for brand_id in sorted(coverage):
        state = coverage[brand_id]
        if state.get('observed_date') != observed_date:
            continue
        items = [item for item in (state.get('surface_items') or []) if item.get('scope_status') == OBSERVED_COUNTED_SCOPE_STATUS]
        if not items:
            continue
        brand_name = state.get('brand_name') or brand_id
        records = [compact_record(brand_id, brand_name, item, observed_date) for item in items]
        for record in records:
            url = record['product_url']
            detail = saved_details.get(brand_id+'|'+url)
            if (not isinstance(detail, dict) or detail.get('product_url') != url
                    or detail.get('source_url') != url or detail.get('publication_status') != 'PUBLISH_HOLD'
                    or detail.get('human_review_required') is not True
                    or detail.get('evidence_level') not in ('OFFICIAL_PRODUCT_JSONLD', CARE_TEXT_SOURCE)):
                continue
            retrieved = detail.get('retrieved_at_utc')
            sha = detail.get('source_sha256')
            claims = detail.get('function_claims')
            if not isinstance(retrieved, str) or not isinstance(sha, str) or len(sha) != 64:
                continue
            if any(char not in '0123456789abcdef' for char in sha):
                continue
            try:
                at = datetime.fromisoformat(retrieved.replace('Z', '+00:00'))
            except ValueError:
                continue
            if at.tzinfo is None or at.astimezone(timezone(timedelta(hours=9))).date().isoformat() != observed_date:
                continue
            if (not record['material_composition'] and detail.get('composition_evidence') == 'OFFICIAL_MATCHING_PRODUCT_TABLE'
                    and isinstance(detail.get('composition'), str) and detail['composition'].strip()):
                record['material_composition'] = detail['composition']
                record['composition_detail_evidence'] = {'source_url': url, 'source_sha256': sha, 'retrieved_at_utc': retrieved}
            care = care_observation(detail)
            if care:
                record['care_label'] = care
            if not isinstance(claims, list) or not claims or not all(isinstance(claim, str) and claim.strip() for claim in claims):
                continue
            record['function_claims'] = list(dict.fromkeys([*record['function_claims'], *claims]))
            record['function_detail_evidence'] = {'source_url': url, 'source_sha256': sha, 'retrieved_at_utc': retrieved}
        for record in records:
            attach_world_review(record, world_reviews, observed_date, same_day=True)
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
    sources = json.loads((COLLECTOR_CONFIG/'brand64-free-direct-sources.json').read_text())['brands']
    world_reviews = world_care_reviews(sources)
    for row in known.values():
        if isinstance(row, dict):
            add_world_listing_features(row, sources.get(row.get('brand_id'), {}))
    latest_path = root/'latest.json'
    feed_path = root/'feed.json'
    if not latest_path.is_file() or not feed_path.is_file():
        raise ValueError('latest.json and feed.json are required for an atomic canonical snapshot')
    latest = json.loads(latest_path.read_text())
    feed = json.loads(feed_path.read_text())
    observation_date = latest.get('observed_date') or latest.get('observation_date')
    if not observation_date:
        raise ValueError('latest.json has no observation date')
    if (feed.get('summary') or {}).get('observed_date') != observation_date:
        raise ValueError('feed.json observation date does not match latest.json')
    output = root/CUMULATIVE_DIR
    output.mkdir(parents=True, exist_ok=True)
    grouped = {}
    for record in known.values():
        if not isinstance(record, dict):
            continue
        brand_id = record.get('brand_id') or ''
        product_url = record.get('product_url') or ''
        if not brand_id or not product_url or record.get('scope_status') not in CUMULATIVE_COUNTED_SCOPE_STATUSES:
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
            attach_world_review(item, world_reviews, observation_date, same_day=False)
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
        brand = {'brand_id': brand_id, 'brand_name': brand_name, 'product_count': len(records), 'path': relative, 'sha256': hashlib.sha256((root/relative).read_bytes()).hexdigest()}
        generated.extend(add_canonical_chunks(root, brand))
        manifest_brands.append(brand)
        cumulative_count += len(records)
    manifest = {
        'format': 'KC_BRAND64_CUMULATIVE_PRODUCTS_INDEX', 'schema_version': '1.3',
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
        'daily_sources': {
            'latest': {'path': 'latest.json', 'sha256': hashlib.sha256(latest_path.read_bytes()).hexdigest()},
            'feed': {'path': 'feed.json', 'sha256': hashlib.sha256(feed_path.read_bytes()).hexdigest()},
        },
    }
    identity_review = {r['identity_key']: r for r in review if r.get('reason') == 'BRAND_IDENTITY_CONFLICT'}
    manifest['identity_review_product_count'] = sum(r.get('review_status') != 'RESOLVED' for r in identity_review.values())
    manifest['identity_resolved_product_count'] = sum(r.get('review_status') == 'RESOLVED' for r in identity_review.values())
    # The manifest plus checksummed brand shards are the sole product source.
    # Do not also publish an all-products catalogue: it duplicates every row,
    # is easy for consumers to mistake for a second source, and grows without
    # bound. V04 and other views must derive from the manifest's brand paths.
    catalogue_path = output/'catalogue.json'
    if catalogue_path.exists():
        catalogue_path.unlink()
    manifest_relative = f'{CUMULATIVE_DIR}/manifest.json'
    (output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))+'\n')
    exported = read_pool(root)
    for key, row in normalize_identities(previous).items():
        if key not in exported and not retained_doclasse_alias(row, exported) and not any(r.get('identity_key') == key and r.get('record') == row
                                           for r in review if r.get('reason') == 'BRAND_IDENTITY_CONFLICT'):
            raise ValueError('Refusing canonical product loss without exact retained review evidence')
    return [manifest_relative, *generated]


def retained_doclasse_alias(previous, exported):
    """A representative URL may change only with the exact prior facts retained."""
    from run_brand64_free_direct_scan import product_identity
    identity = product_identity(previous)
    if not identity.startswith('doclasse:'): return False
    snapshot = {k:v for k,v in previous.items() if k not in ('legacy_identity_records','source_url_aliases')}
    for row in exported.values():
        if (row.get('brand_id') == previous.get('brand_id') and product_identity(row) == identity and
                previous['product_url'] in row.get('source_url_aliases', []) and
                set(previous.get('source_url_aliases', [])) <= set(row.get('source_url_aliases', [])) and
                all(r in row.get('legacy_identity_records', []) for r in previous.get('legacy_identity_records', [])) and
                snapshot in row.get('legacy_identity_records', [])):
            return True
    return False


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
    write_history(root, read_history(root))
    names = list(dict.fromkeys([*STATE_FILES, *history_files(root), 'feed.json', 'latest.json', 'flash-latest.json', 'summary.md', 'retrospective-merge-summary.json', *generated]))
    for name in names:
        if not (root/name).is_file(): raise ValueError('Missing checkpoint: '+name)
    with tempfile.TemporaryDirectory() as directory:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(directory)/'index')}
        git('read-tree', parent if parent else '--empty', env=env)
        if parent:
            old_parts = git('ls-tree', '-r', '--name-only', parent, '--', PREFIX+HISTORY_DIRECTORY+'/').stdout.splitlines()
            old_parts += [path for path in git('ls-tree', '-r', '--name-only', parent, '--', PREFIX+CUMULATIVE_DIR+'/').stdout.splitlines()
                          if re.fullmatch(re.escape(PREFIX+CUMULATIVE_DIR)+r'/BR-\d{5}\.json\.part-\d{4}', path)]
            for path in old_parts:
                git('update-index', '--force-remove', path, env=env)
        for name in names:
            blob = git('hash-object', '-w', str(root/name)).stdout.strip()
            git('update-index', '--add', '--cacheinfo', '100644', blob, PREFIX+name, env=env)
        git('update-index', '--force-remove', PREFIX+CUMULATIVE_DIR+'/catalogue.json', env=env, check=False)
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
