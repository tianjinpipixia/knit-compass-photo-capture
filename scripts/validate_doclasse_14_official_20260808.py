#!/usr/bin/env python3
import csv
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

BASE = Path('data/brand-research')

def read(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

rows = read('2026-08-08-doclasse-14-official.csv')
work_rows = read('2026-08-08-product78-next-work.csv')

assert len(rows) == 14
assert len({r['staging_product_id'] for r in rows}) == 14
assert Counter(r['official_match_status'] for r in rows) == {
    'EXACT_OFFICIAL_MATCH': 13,
    'OFFICIAL_CURRENT_LISTING_CODE_PENDING': 1,
}
assert all(r['checked_date'] == '2026-08-08' for r in rows)

by_id = {r['staging_product_id']: r for r in rows}
expected_codes = {
    'PRD_DOCLASSE_0090': '32640',
    'PRD_DOCLASSE_0106': '32667',
    'PRD_DOCLASSE_0080': '32673',
    'PRD_DOCLASSE_0084': '32906',
    'PRD_DOCLASSE_0103': '32689',
    'PRD_DOCLASSE_0110': '32896',
    'PRD_DOCLASSE_0115': '32354',
    'PRD_DOCLASSE_0112': '32960',
    'PRD_DOCLASSE_0094': '32861',
    'PRD_DOCLASSE_0089': '32957',
    'PRD_DOCLASSE_0113': '32676',
    'PRD_DOCLASSE_0114': '32682',
    'PRD_DOCLASSE_0087': '32693',
}
for pid, code in expected_codes.items():
    row = by_id[pid]
    assert row['official_code'] == code
    parsed = urlparse(row['official_url'])
    assert parsed.scheme == 'https'
    assert parsed.netloc == 'www.doclasse.com'
    assert code in row['official_url']

emb = by_id['PRD_DOCLASSE_0108']
assert emb['official_code'] == ''
assert emb['official_match_status'] == 'OFFICIAL_CURRENT_LISTING_CODE_PENDING'
assert urlparse(emb['official_url']).netloc == 'www.doclasse.com'

uv = by_id['PRD_DOCLASSE_0090']
assert uv['official_composition'] == 'カーディガン: ポリエステル59%・レーヨン41% / プルオーバー: ポリエステル52%・レーヨン36%・ナイロン12%'
assert set(uv['official_functions'].split('; ')) == {'紫外線90%以上カット', '洗濯機可'}
assert all(r['official_composition'] == '' for r in rows if r['staging_product_id'] != 'PRD_DOCLASSE_0090')

work = {r['work_bucket']: int(r['count']) for r in work_rows}
assert work['NO_URL_ROPE_PICNIC_OFFICIAL_MATCHED'] == 22
assert work['NO_URL_DOCLASSE_OFFICIAL_MATCHED'] == 13
assert work['NO_URL_DOCLASSE_CODE_PENDING'] == 1
assert work['NO_URL_TARGET_PENDING'] == 9
assert sum(v for k, v in work.items() if k.startswith('NO_URL_')) == 45
assert sum(v for k, v in work.items() if k != 'TOTAL') == 78

print('DoCLASSE 14 official: OK (13 exact codes + 1 current listing code pending; remaining no-URL backlog=9)')
