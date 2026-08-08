#!/usr/bin/env python3
import csv
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

BASE = Path('data/brand-research')

def read(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

summary = read('2026-08-08-product78-triage-summary.csv')
out = read('2026-08-08-product78-out-of-scope.csv')
verified = read('2026-08-08-product-verification-batch1.csv')

total = next(r for r in summary if r['brand_name'] == 'TOTAL')
assert int(total['total']) == 78
assert int(total['target_or_scope_review']) == 64
assert int(total['women_subline']) == 1
assert int(total['out_kids']) == 8
assert int(total['out_junior']) == 4
assert int(total['out_mens']) == 1
assert int(total['official_url_present']) == 33
assert int(total['no_url']) == 45
assert int(total['review_required']) == 75
assert int(total['verified_public']) == 2
assert int(total['owner_confirmed']) == 1
assert 64 + 1 + 8 + 4 + 1 == 78

assert len(out) == 13
scope_counts = Counter(r['research_scope'] for r in out)
assert scope_counts == {
    'OUT_OF_SCOPE_KIDS': 8,
    'OUT_OF_SCOPE_JUNIOR_LINE': 4,
    'OUT_OF_SCOPE_MENS': 1,
}
assert {r['product_id'] for r in out if r['research_scope'] == 'OUT_OF_SCOPE_MENS'} == {'PRD_GU_360832'}
assert all(r['action'] == 'RETAIN_HISTORY_EXCLUDE_FROM_WOMEN_RESEARCH' for r in out)

assert len(verified) == 10
assert Counter(r['brand_name'] for r in verified) == {'GLOBAL WORK': 8, 'DoCLASSE': 2}
assert all(r['checked_date'] == '2026-08-08' for r in verified)
for row in verified:
    parsed = urlparse(row['official_url'])
    assert parsed.scheme == 'https'
    assert parsed.netloc in {'www.dot-st.com', 'www.doclasse.com'}

by_code = {r['product_code']: r for r in verified}
assert by_code['149911']['current_scope'] == 'WOMEN_MATINEE_LINE'
assert by_code['32692']['official_composition'] == 'レーヨン53%・ポリエステル32%・ナイロン15%'
assert by_code['32669']['official_composition'] == 'レーヨン63%・ナイロン37%'
for claim in ('95%以上UVカット', '接触冷感', '洗濯機OK', '遮熱', '抗菌防臭'):
    assert claim in by_code['32669']['official_functions']
assert by_code['32669']['change_required'] == 'UPDATE_FUNCTION_EVIDENCE_PRICE_OBSERVATION_ONLY'

print('product78 triage: OK (78 total / 13 clear out-of-scope / 10 first official checks)')
