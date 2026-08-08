#!/usr/bin/env python3
import csv
from pathlib import Path
from urllib.parse import urlparse

PATH = Path('data/brand-research/2026-08-08-official-verification-batch1.csv')
with PATH.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))

expected_ids = {
    'BR-00001','BR-00002','BR-00003','BR-00004','BR-00005','BR-00006','BR-00007','BR-00008',
    'BR-00009','BR-00010','BR-00011','BR-00012','BR-00013','BR-00014','BR-00015','BR-00016',
    'BR-00018','BR-00019','BR-00020','BR-00058','BR-00059','BR-00061','BR-00063','BR-00064',
}
assert len(rows) == 24
assert {r['canonical_brand_id'] for r in rows} == expected_ids
assert len({r['canonical_brand_id'] for r in rows}) == 24
assert all(r['checked_date'] == '2026-08-08' for r in rows)

allowed_domains = {
    'www.uniqlo.com','www.gu-global.com','www.muji.com','www.ropepicnic.com','www.jun.co.jp',
    'www.adastria.co.jp','www.stripe-intl.com','stripe-club.com','store.world.co.jp',
    'www.cox-online.co.jp','www.doclasse.com','any-onward.com','www.canshop.jp','www.dot-st.com',
}
for row in rows:
    for key in ('official_brand_url','official_knit_url'):
        url = row[key].strip()
        if not url:
            continue
        parsed = urlparse(url)
        assert parsed.scheme == 'https'
        assert parsed.netloc in allowed_domains, (row['canonical_brand_id'], parsed.netloc)

by_id = {r['canonical_brand_id']: r for r in rows}
assert by_id['BR-00020']['verification_status'] == 'VERIFIED_LEGACY_REBRANDED'
assert by_id['BR-00020']['current_women_scope'] == 'LEGACY'
assert by_id['BR-00059']['verification_status'] == 'VERIFIED_OFFICIAL_CURRENT'
assert by_id['BR-00061']['verification_status'] == 'VERIFIED_SUBLINE'
assert by_id['BR-00061']['official_brand_url'].startswith('https://www.dot-st.com/globalwork/')
assert by_id['BR-00013']['official_knit_url'].startswith('https://store.world.co.jp/s/brand/index/')
assert by_id['BR-00014']['official_knit_url'].startswith('https://store.world.co.jp/s/brand/shoo-la-rue/')

print('brand64 official verification batch1: OK (24 official identity/scope checks)')
