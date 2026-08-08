#!/usr/bin/env python3
import csv
from pathlib import Path
from urllib.parse import urlparse

B1 = Path('data/brand-research/2026-08-08-official-verification-batch1.csv')
B2 = Path('data/brand-research/2026-08-08-official-verification-batch2.csv')

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

b1 = read(B1)
b2 = read(B2)
assert len(b1) == 24
assert len(b2) == 40
ids1 = {r['canonical_brand_id'] for r in b1}
ids2 = {r['canonical_brand_id'] for r in b2}
assert not ids1 & ids2
assert ids1 | ids2 == {f'BR-{n:05d}' for n in range(1, 65)}
assert len({r['canonical_brand_id'] for r in b2}) == 40
assert all(r['checked_date'] == '2026-08-08' for r in b2)

allowed_domains = {
    'www.coen.co.jp', 'www.adastria.co.jp', 'www.stripe-intl.com',
    'crosset.onward.co.jp', 'store.world.co.jp', 'store.saneibd.com',
    'www.urban-research.jp', 'baycrews.jp', 'store.united-arrows.co.jp',
    'www.muji.com', 'usagi-online.com',
}
for row in b2:
    for key in ('official_brand_url', 'official_knit_url'):
        url = row[key].strip()
        if not url:
            continue
        parsed = urlparse(url)
        assert parsed.scheme == 'https', (row['canonical_brand_id'], url)
        assert parsed.netloc in allowed_domains, (row['canonical_brand_id'], parsed.netloc)

by_id = {r['canonical_brand_id']: r for r in b2}
assert by_id['BR-00043']['official_brand_url'] == 'https://crosset.onward.co.jp/shop/jpress-ladies/'
assert by_id['BR-00043']['current_women_scope'] == 'YES'
for brand_id in ('BR-00044', 'BR-00048'):
    assert by_id[brand_id]['current_women_scope'] == 'NO'
    assert by_id[brand_id]['verification_status'] == 'VERIFIED_OFFICIAL_CURRENT_MENS_EXCLUDED'
assert by_id['BR-00060']['official_brand_url'] == 'https://www.muji.com/jp/ja/special-feature/clothes/mujilabo/'
assert by_id['BR-00062']['official_brand_url'] == 'https://usagi-online.com/brand/milaowen/'
assert by_id['BR-00029']['current_women_scope'] == 'GIRLS_TEEN'

scope_pending = {r['canonical_brand_id'] for r in b2 if r['verification_status'] == 'VERIFIED_OFFICIAL_CURRENT_SCOPE_PENDING'}
assert scope_pending == {'BR-00023','BR-00025','BR-00027','BR-00028','BR-00030','BR-00032','BR-00033','BR-00034'}

print('brand64 official verification batch2: OK (40 remaining checks; 64/64 identities covered)')
