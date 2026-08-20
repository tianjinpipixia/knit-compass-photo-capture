#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1] if len(sys.argv)==1 else Path(sys.argv[1]).resolve()

def require(path,*needles):
    text=(ROOT/path).read_text(encoding='utf-8')
    missing=[n for n in needles if n not in text]
    if missing: raise SystemExit(f'{path}: missing {missing}')

require('brand-intelligence/brand-diff-auto-intake.js',
        "review_status:'PENDING'","automatic_master_promotion:'FORBIDDEN'",
        'NATURAL BEAUTY BASIC','https://mix.tokyo/pages/naturalbeautybasic',"productUrl:''")
require('yarn-process-fields-v1.js','preSpinningPreparation','spinningMethodRaw','mvs_vortex','air_jet','oe_rotor','IDBObjectStore.prototype.add')
require('brand-intelligence/yarn-process-master-v1.js','preSpinningPreparation','spinningMethodRaw','applyPayloadFields','kc_yarn_process_fields_')
require('yarn-taxonomy-guard.js','yarn-process-fields-v1.js')
require('brand-intelligence/owner-observed-products.js','brand-diff-auto-intake.js','yarn-process-master-v1.js')
print('validate_brand_diff_yarn_process: PASS')
