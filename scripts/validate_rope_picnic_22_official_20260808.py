#!/usr/bin/env python3
import csv
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

PATH = Path('data/brand-research/2026-08-08-rope-picnic-22-official.csv')
NEXT = Path('data/brand-research/2026-08-08-product78-next-work.csv')
with PATH.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))

assert len(rows) == 22
assert len({r['staging_product_id'] for r in rows}) == 22
assert len({r['official_code'] for r in rows}) == 21
assert all(r['checked_date'] == '2026-08-08' for r in rows)

status = Counter(r['official_match_status'] for r in rows)
assert status == {'EXACT_OFFICIAL_MATCH': 20, 'POSSIBLE_DUPLICATE_SAME_OFFICIAL_PRODUCT': 2}, status

for row in rows:
    parsed = urlparse(row['official_url'])
    assert parsed.scheme == 'https'
    assert parsed.netloc == 'www.junonline.jp'
    assert row['official_code'] in row['official_url']
    assert row['official_composition']

by_code = {}
for row in rows:
    by_code.setdefault(row['official_code'], []).append(row)

assert len(by_code['GDK16500']) == 2
assert {r['staging_product_id'] for r in by_code['GDK16500']} == {
    'TMP_NBR_BRNC_0003_0003', 'PRD_ROPE_PICNIC_018'
}
assert all('HUMAN_REVIEW_DUPLICATE' in r['change_required'] for r in by_code['GDK16500'])
assert all(len(v) == 1 for k, v in by_code.items() if k != 'GDK16500')

single = {k: v[0] for k, v in by_code.items() if len(v) == 1}
assert single['GDM16600']['official_composition'] == 'ポリエステル75%・レーヨン25%'
assert single['GDM16560']['official_composition'] == 'レーヨン68%・アクリル18%・ナイロン9%・ポリエステル5%'
assert single['GDM16140']['official_composition'] == 'レーヨン56%・アクリル29%・ポリエステル8%・ナイロン7%'
assert single['GDM16290']['official_composition'] == 'ポリエステル70%・再生繊維（セルロース）30%'
assert single['GDM16120']['official_composition'] == 'レーヨン65%・ナイロン27%・ポリエステル8%'
assert 'プレーティング' in single['GDM16120']['official_structure_note']
assert single['GDM16390']['official_composition'] == 'レーヨン65%・ポリエステル35%'
assert single['GDM16250']['official_composition'] == 'ポリエステル100%'
assert single['GDK16400']['official_composition'] == 'ポリエステル70%・レーヨン30%'
assert set(single['GDK16400']['official_functions'].split('; ')) == {'UVカット','吸水速乾','遮熱'}
assert single['GDM16550']['official_composition'] == 'レーヨン66%・ナイロン34%'
assert single['GDM16520']['official_composition'] == 'レーヨン65%・ナイロン35%'
assert single['GDM16500']['official_composition'] == 'レーヨン65%・ナイロン35%'
assert '紫外線遮蔽率90%以上' in single['GDM16500']['official_functions']
assert '近赤外線ケア(遮蔽率80.0%)' in single['GDM16500']['official_functions']

with NEXT.open(encoding='utf-8-sig', newline='') as f:
    work_rows = list(csv.DictReader(f))
work = {r['work_bucket']: int(r['count']) for r in work_rows}
assert work == {
    'OUT_OF_SCOPE_HISTORY': 13,
    'EXISTING_OFFICIAL_URL_CURRENT_EVIDENCE': 14,
    'EXISTING_OFFICIAL_URL_RECHECK_PENDING': 6,
    'NO_URL_ROPE_PICNIC_OFFICIAL_MATCHED': 22,
    'NO_URL_TARGET_PENDING': 23,
    'TOTAL': 78,
}
assert 13 + 14 + 6 + 22 + 23 == 78

print('ROPÉ PICNIC 22 official: OK (22 staging rows -> 21 official products; 1 duplicate pair held; remaining no-URL backlog=23)')
