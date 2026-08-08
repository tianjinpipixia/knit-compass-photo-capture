#!/usr/bin/env python3
import csv
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

BASE = Path('data/brand-research')

def read(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

b1 = read('2026-08-08-product-verification-batch1.csv')
b2 = read('2026-08-08-product-verification-batch2.csv')
next_work = read('2026-08-08-product78-next-work.csv')

assert len(b1) == 10
assert len(b2) == 10
assert len({r['product_id'] for r in b1 + b2}) == 20
assert Counter(r['brand_name'] for r in b2) == {'Te chichi': 6, 'DoCLASSE': 4}

by_code = {r['product_code']: r for r in b2}
assert by_code['32660']['verification_result'] == 'VERIFIED_OFFICIAL_CURRENT'
assert by_code['32660']['official_composition'] == 'プルオーバー: レーヨン82%・ポリエステル18% / インナー: レーヨン60%・ナイロン23%・ポリエステル14%・ポリウレタン3%'
assert '1本取り' in by_code['32660']['official_functions']
assert 'プレーティング' in by_code['32660']['official_functions']
assert by_code['32956']['official_composition'] == 'ポリエステル50%・レーヨン32%・ナイロン15%・ポリウレタン3%'
assert by_code['32668']['verification_result'] == 'VERIFIED_OFFICIAL_CURRENT_CATEGORY'
assert by_code['32668']['official_composition'] == ''
assert by_code['33048']['verification_result'] == 'VERIFIED_OFFICIAL_CURRENT_CATEGORY'
assert by_code['33048']['official_composition'] == ''
assert all(by_code[c]['observed_price_yen'] == '' for c in ('32660','32956','32668','33048'))

techichi = [r for r in b2 if r['brand_name'] == 'Te chichi']
assert len(techichi) == 6
assert all(r['verification_result'] == 'OFFICIAL_URL_RECHECK_PENDING' for r in techichi)
assert all(urlparse(r['official_url']).netloc == 'www.canshop.jp' for r in techichi)
assert by_code['2601404-21-12']['change_required'] == 'HOLD_COMPOSITION_CONFLICT_NO_CORE_UPDATE'

for row in b2:
    parsed = urlparse(row['official_url'])
    assert parsed.scheme == 'https'
    assert parsed.netloc in {'www.doclasse.com','www.canshop.jp'}
    assert row['checked_date'] == '2026-08-08'

# These are invariant totals from the original 78-row triage. The 45 no-URL
# records are progressively split into DONE/PENDING buckets by later batches,
# so do not freeze their internal bucket names here.
work = {r['work_bucket']: int(r['count']) for r in next_work}
assert work['OUT_OF_SCOPE_HISTORY'] == 13
assert work['EXISTING_OFFICIAL_URL_CURRENT_EVIDENCE'] == 14
assert work['EXISTING_OFFICIAL_URL_RECHECK_PENDING'] == 6
assert work['TOTAL'] == 78
assert sum(v for k, v in work.items() if k != 'TOTAL') == 78
assert sum(v for k, v in work.items() if k.startswith('NO_URL_')) == 45
assert 14 + 6 == 20

print('product78 official batch2: OK (20 existing-URL target records remain stable; no-URL 45 may progress across later buckets)')
