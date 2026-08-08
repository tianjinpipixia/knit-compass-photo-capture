#!/usr/bin/env python3
import csv
from collections import Counter
from pathlib import Path

PATH = Path('data/brand-research/2026-08-08-brand64-progress.csv')
with PATH.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))

assert len(rows) == 64, f'expected 64 brands, got {len(rows)}'
ids = [r['canonical_brand_id'] for r in rows]
assert len(ids) == len(set(ids)) == 64
assert ids == [f'BR-{n:05d}' for n in range(1,65)]
assert sum(int(r['product_records_count']) for r in rows) == 78
assert sum(r['priority20_staged'] == 'YES' for r in rows) == 20

phases = Counter(r['research_phase'] for r in rows)
expected = {
    'MASTER_ONLY_UNCHECKED': 39,
    'PRIORITY20_STAGED': 15,
    'PRODUCT_EVIDENCE_PRESENT': 6,
    'EXCLUDED_MENS_ONLY': 2,
    'IDENTITY_REVIEW_REQUIRED': 2,
}
assert dict(phases) == expected, (phases, expected)

assert {r['canonical_brand_id'] for r in rows if r['research_phase']=='EXCLUDED_MENS_ONLY'} == {'BR-00044','BR-00048'}
assert {r['canonical_brand_id'] for r in rows if r['research_phase']=='IDENTITY_REVIEW_REQUIRED'} == {'BR-00059','BR-00061'}
assert {r['canonical_brand_id'] for r in rows if int(r['product_records_count']) > 0} == {'BR-00002','BR-00003','BR-00004','BR-00006','BR-00018','BR-00058'}

print('brand64 progress: OK (64 master / 20 staged / 78 product rows)')
