#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
schema=json.loads((ROOT/'config/materials-db-schema.json').read_text(encoding='utf-8'))
assert schema['format']=='KC_MATERIALS_DB_SCHEMA'
assert schema['policy']['human_review_before_confirmed_master'] is True
assert schema['policy']['automatic_product_claim_inheritance']=='FORBIDDEN'
assert {'fiber_generic','branded_fiber','polymer','functional_technology','processing_technology'} <= set(schema['material_type_enum'])

framework=json.loads((ROOT/'data/sales-story/sales-story-framework.json').read_text(encoding='utf-8'))
assert framework['format']=='KC_SALES_STORY_FRAMEWORK'
assert framework['guardrails']['sales_quantity_estimation']=='FORBIDDEN'
assert {row['id'] for row in framework['templates']}=={'SS-T01','SS-T02','SS-T03'}

research=json.loads((ROOT/'data/yarn-research/2026-08-20-r80-pet20-core-spun.json').read_text(encoding='utf-8'))
assert research['status']=='CANDIDATE_FOUND_NEEDS_POLYESTER_SUBTYPE_CONFIRMATION'
hongde=next(row for row in research['candidates'] if row['supplier']=='广东鸿德纺织品有限公司')
assert hongde['composition']=='80%粘胶 / 20%涤纶'
assert any('PET' in q and 'PBT' in q for q in hongde['open_questions'])
assert research['boundary']['do_not_promote_to_confirmed_yarn_master_before_reply'] is True

rows=[json.loads(line) for line in (ROOT/'data/brand-md-monitoring/2026-08-20-nbb-live-products.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
assert len(rows)==3 and all(row['b']=='NATURAL BEAUTY BASIC' for row in rows)
dolman=next(row for row in rows if row['code']=='0176275661')
assert dolman['composition_raw']=='レーヨン63% / ナイロン37%'
assert {'UVカット','マシンウォッシャブル','接触冷感'} <= set(dolman['function'])
assert all(row['p']=='HOLD' for row in rows)

for rel in ('brand-intelligence/materials-db-v1.js','brand-intelligence/sales-story-v1.js'):
    text=(ROOT/rel).read_text(encoding='utf-8')
    assert 'kc_independent_practical_v0_4' in text
loader=(ROOT/'brand-intelligence/owner-observed-products.js').read_text(encoding='utf-8')
assert './materials-db-v1.js?v=1.0.0' in loader
assert './sales-story-v1.js?v=1.0.0' in loader
print('OK: Materials DB v1, Sales Story v1, NBB live snapshot, and R80/PET20 research validated')
