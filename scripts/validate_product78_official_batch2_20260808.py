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

work = {r['work_bucket']: int(r['count']) for r in next_work}
assert work == {
    'OUT_OF_SCOPE_HISTORY': 13,
    'EXISTING_OFFICIAL_URL_CURRENT_EVIDENCE': 14,
    'EXISTING_OFFICIAL_URL_RECHECK_PENDING': 6,
    'NO_URL_TARGET_PENDING': 45,
    'TOTAL': 78,
}
assert 13 + 14 + 6 + 45 == 78
assert 14 + 6 == 20

print('product78 official batch2: OK (all 20 target records with existing URLs processed; next=45 no-URL targets)')
