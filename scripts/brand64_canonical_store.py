"""Lossless, validated canonical Brand64 records; all other stores are inputs/views."""
import hashlib
import json
from pathlib import Path

REPOSITORY = 'tianjinpipixia/knit-compass-photo-capture'
BRANCH = 'brand64/flash-feed'
PREFIX = 'data/brand-md-monitoring/direct-scans/'
CANONICAL = {'repository': REPOSITORY, 'branch': BRANCH,
             'path': PREFIX + 'cumulative-products/manifest.json',
             'role': 'SOLE_PRODUCT_SOURCE', 'identity': 'brand_id|product_url'}


def read_pool(root):
    """A present but incomplete/corrupt canonical snapshot must fail closed."""
    path = root / 'cumulative-products/manifest.json'
    if not path.exists():
        return None
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('format') != 'KC_BRAND64_CUMULATIVE_PRODUCTS_INDEX':
        raise ValueError('Invalid canonical manifest')
    records = {}
    brands = set()
    for brand in manifest['brands']:
        bid = brand['brand_id']
        if bid in brands or brand['path'] != f'cumulative-products/{bid}.json' or '/' in bid or '..' in bid:
            raise ValueError('Invalid canonical brand/path')
        brands.add(bid)
        raw = (root / brand['path']).read_bytes()
        if brand.get('sha256') and hashlib.sha256(raw).hexdigest() != brand['sha256']:
            raise ValueError('Canonical shard checksum mismatch')
        shard = json.loads(raw)
        if shard['brand_id'] != bid or shard['observation_date'] != manifest['observation_date']:
            raise ValueError('Canonical shard generation mismatch')
        if len(shard['records']) != brand['product_count']:
            raise ValueError('Canonical shard count mismatch')
        for row in shard['records']:
            if row['brand_id'] != bid or not row.get('product_url') or not row.get('product_name'):
                raise ValueError('Invalid canonical product')
            key = bid + '|' + row['product_url']
            if key in records:
                raise ValueError('Duplicate canonical product')
            records[key] = row
    if len(records) != manifest['cumulative_unique_product_count']:
        raise ValueError('Canonical total mismatch')
    return records


def preserve(previous, incoming):
    """Keep old products and evidence; a stale checkpoint cannot replace newer fields."""
    merged = dict(previous)
    for key, row in incoming.items():
        old = merged.get(key)
        if not old:
            merged[key] = row
            continue
        fresh = str(row.get('last_seen_date') or '') >= str(old.get('last_seen_date') or '')
        result = {**old, **{k: v for k, v in row.items() if v not in (None, '', [], {}) and (fresh or not old.get(k))}}
        for field in ('retrospective_months', 'retrospective_sources', 'retrospective_evidence', 'function_claims', 'source_provenance', 'source_url_aliases', 'legacy_identity_records'):
            values = list(old.get(field) or [])
            for value in row.get(field) or []:
                if value not in values:
                    values.append(value)
            if values:
                result[field] = values
        for field, operation in [('first_seen_date', min), ('last_seen_date', max)]:
            dates = [x for x in (old.get(field), row.get(field)) if x]
            if dates:
                result[field] = operation(dates)
        merged[key] = result
    return merged


def normalize_identities(records):
    """Coalesce slash aliases, retaining both their URLs and complete prior facts."""
    result = {}
    for old_key, original in sorted(records.items()):
        row = dict(original)
        url = str(row.get('product_url') or '').rstrip('/')
        if not url:
            continue
        key = str(row.get('brand_id') or '') + '|' + url
        row['product_url'] = url
        aliases = list(row.get('source_url_aliases') or [])
        if url not in aliases:
            aliases.append(url)
        if original['product_url'] not in aliases:
            aliases.append(original['product_url'])
        row['source_url_aliases'] = aliases
        if key in result:
            prior = result[key]
            preserved = list(prior.get('legacy_identity_records') or [])
            for source in [prior, original]:
                record = {k: v for k, v in source.items() if k not in ('legacy_identity_records', 'source_url_aliases')}
                if record not in preserved:
                    preserved.append(record)
            row['legacy_identity_records'] = preserved
        result = preserve(result, {key: row})
    return result


def seed_working_state(root):
    canonical = read_pool(root)
    path = root / 'known-products.json'
    working = normalize_identities(json.loads(path.read_text()) if path.exists() else {})
    if canonical is not None:
        working = preserve(normalize_identities(canonical), normalize_identities(working))
    path.write_text(json.dumps(working, ensure_ascii=False, separators=(',', ':')) + '\n')
    return working


def attach_details(known, details):
    for key, detail in details.items():
        row = known.get(key.rstrip('/'))
        if (not row or detail.get('product_url') not in [row['product_url'], *row.get('source_url_aliases', [])]
            or detail.get('source_url') != detail.get('product_url')
            or detail.get('publication_status') != 'PUBLISH_HOLD'
            or detail.get('human_review_required') is not True
            or not str(detail.get('evidence_level', '')).startswith('OFFICIAL_PRODUCT_')):
            continue
        previous = row.get('official_detail') or {}
        if str(detail.get('retrieved_at_utc', '')) >= str(previous.get('retrieved_at_utc', '')):
            row['official_detail'] = detail
        if not row.get('material_composition') and detail.get('composition'):
            row['material_composition'] = detail['composition']
    return known
