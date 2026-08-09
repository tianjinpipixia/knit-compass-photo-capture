#!/usr/bin/env python3
import json
from pathlib import Path

PATH = Path('data/manual-intake/2026-08-08-weijie-hesheng-batch1.json')
data = json.loads(PATH.read_text(encoding='utf-8'))

assert data['format'] == 'KC_V04_INBOX_EXPORT'
assert data['schema_version'] == '1.0'
items = data['items']
assert len(items) == 10
assert len({item['dedupe_key'] for item in items}) == 10
assert all(item['format'] == 'KC_V04_INBOX_ITEM' for item in items)
assert all(item['review_status'] == 'PENDING' for item in items)
assert all(item['payload']['targetType'] == 'yarn' for item in items)
assert all(item['payload']['compositionTotal'] == 100 for item in items)
assert all(item['payload']['compositionStatus'] == 'confirmed' for item in items)
assert all(item['payload']['verificationStatus'] == 'confirmed' for item in items)
assert all(item['payload']['sourceType'] == 'user_photo_supplier_document' for item in items)

weijie = [item for item in items if item['payload']['sourceOrganizationName'] == '苏州维杰纺织有限公司']
hesheng = [item for item in items if item['payload']['sourceOrganizationName'] == '东莞市合升纺织品有限公司']
assert len(weijie) == 5
assert len(hesheng) == 5
assert len({item['payload']['sourceOrganizationId'] for item in weijie}) == 1
assert len({item['payload']['sourceOrganizationId'] for item in hesheng}) == 1

expected = {
    ('TL-2251', '2/32NM', 'PBT 20% / Wool 10% / Polyester 49% / Acrylic 21%'),
    ('TL-1352', '2/32NM', 'Acrylic 29% / Viscose 37% / Cotton 16% / PTT 18%'),
    ('TL-1353', '2/48NM', 'Acrylic 25% / Viscose 33% / Cotton 14% / PTT 28%'),
    ('TL-1502', '2/50NM', 'Viscose 72% / PBT 28%'),
    ('TL-1530', '2/50NM', 'Viscose 70% / PTT 30%'),
    ('纳米丝麻棉（全精梳）', '2/80NM', 'Cotton 78% / Polyester 22%'),
    ('48支纳米丝麻棉', '2/48NM', 'Cotton 88% / Polyester 12%'),
    ('58支纳米丝麻棉', '2/58NM', 'Cotton 85% / Polyester 15%'),
    ('超高捻仿亚麻', '1/24NM', 'Viscose 89% / Nylon 11%'),
    ('高端亚麻爽', '1/24NM', 'Viscose 89% / Polyester 11%'),
}
actual = {(i['payload']['yarnName'], i['payload']['countDisplay'], i['payload']['compositionRaw']) for i in items}
assert actual == expected

for item in items:
    p = item['payload']
    assert p['photoRefs'] and p['photoRefs'][0]['fileName']
    assert '根拠写真:' in p['notes']
    assert p['basicYarnForm'] == 'unconfirmed'
    assert p['yarnStructure'] == ''
    assert p['spinningMethod'] == ''
    assert p['processingMethod'] == ''
    assert 'salesQuantity' not in p

print('manual intake batch1: OK (10 PENDING yarn candidates)')
