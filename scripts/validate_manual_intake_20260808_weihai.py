#!/usr/bin/env python3
import json
from pathlib import Path

PATH = Path('data/manual-intake/2026-08-08-weihai-yaxin-chengyun-batch2.json')
data = json.loads(PATH.read_text(encoding='utf-8'))

assert data['format'] == 'KC_V04_INBOX_EXPORT'
assert data['schema_version'] == '1.0'
items = data['items']
assert len(items) == 2
assert len({item['dedupe_key'] for item in items}) == 2
assert all(item['format'] == 'KC_V04_INBOX_ITEM' for item in items)
assert all(item['review_status'] == 'PENDING' for item in items)
assert all(item['payload']['targetType'] == 'organization' for item in items)
assert all(item['payload']['commonIds']['researchId'].startswith('TMP-RS-') for item in items)
assert all(item['payload']['verificationStatus'] == 'confirmed' for item in items)

by_name = {item['payload']['sourceOrganizationName']: item['payload'] for item in items}
assert set(by_name) == {'威海雅信纺织服装有限公司', '威海诚韵国际贸易有限公司'}

yaxin = by_name['威海雅信纺织服装有限公司']
chengyun = by_name['威海诚韵国际贸易有限公司']

assert yaxin['organizationProfile']['legalNameEnglish'] == 'WEIHAI YAXIN TEXTILE & GARMENTS CO., LTD.'
assert yaxin['organizationProfile']['organizationType'] == 'knitwear_manufacturer'
assert yaxin['organizationProfile']['foundedYear'] == 2009
assert yaxin['organizationProfile']['contacts'][0]['name'] == '丁晓威'
assert yaxin['organizationProfile']['contacts'][0]['wechat'] == 'W102761652'
assert yaxin['organizationProfile']['contacts'][0]['affiliationStatus'] == 'confirmed_with_yaxin'

assert chengyun['organizationProfile']['legalNameEnglish'] == 'WEIHAI CHENGYUN INTERNATIONAL TRADE CO., LTD.'
assert chengyun['organizationProfile']['organizationType'] == 'trading_company'
assert chengyun['organizationProfile']['foundedYear'] == 2004
assert chengyun['organizationProfile']['ownerProvidedEmail'] == 'admin@cheng-yun.com'
assert chengyun['organizationProfile']['contacts'][0]['affiliationStatus'] == 'related_contact_only_not_confirmed_employee_of_chengyun'

for payload in (yaxin, chengyun):
    relationship = payload['organizationProfile']['relationships'][0]
    assert relationship['relationshipType'] == 'operationally_related'
    assert relationship['capitalRelationshipStatus'] == 'unconfirmed'
    assert relationship['parentDirectionStatus'] == 'not_asserted_in_master'
    assert 'THERMO WALKER®' in payload['organizationProfile']['linkedMaterials']
    assert 'WARMPLUS-R' in payload['organizationProfile']['linkedMaterials']
    assert set(payload['organizationProfile']['linkedDocuments']) == {
        'WARMPLUS-R吸湿発熱2019.pdf',
        'WARMPLUS-R抗ピリング.pdf',
        'QD-24-072239.pdf',
    }
    assert payload['sourceUrl'] == 'https://www.cheng-yun.com/'

assert yaxin['targetId'] != chengyun['targetId']
assert yaxin['sourceOrganizationId'] != chengyun['sourceOrganizationId']
assert yaxin['organizationProfile']['relationships'][0]['relatedOrganizationTempId'] == chengyun['targetId']
assert chengyun['organizationProfile']['relationships'][0]['relatedOrganizationTempId'] == yaxin['targetId']
assert all('relatedOrganizationId' not in payload['organizationProfile']['relationships'][0] for payload in (yaxin, chengyun))

print('manual intake Weihai batch2: OK (2 separate PENDING organizations + reciprocal temp relations ready for formal ID resolution)')
