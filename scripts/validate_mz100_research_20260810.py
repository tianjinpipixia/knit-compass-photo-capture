#!/usr/bin/env python3
"""Validate MZ100 research evidence and its Human Review-only inbox batch."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "data/yarn-research/2026-08-10-mz100-evidence.json"
INTAKE_PATH = ROOT / "data/manual-intake/2026-08-10-mz100-yarn-research-batch3.json"
HUMAN_REVIEW_PATH = ROOT / "brand-intelligence/index-current.html"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def percent_total(value):
    return sum(float(number) for number in re.findall(r"(\d+(?:\.\d+)?)\s*[%％]", value))


evidence_bundle = load(EVIDENCE_PATH)
intake = load(INTAKE_PATH)

assert evidence_bundle["format"] == "KC_RESEARCH_EVIDENCE_BUNDLE"
assert evidence_bundle["schema_version"] == "1.0"
assert evidence_bundle["batch_id"] == "KC-RESEARCH-20260810-MZ100"

boundary = evidence_bundle["safety_boundary"]
assert boundary == {
    "master_promotion_performed": False,
    "human_review_required": True,
    "production_connection_added": False,
    "core_connection_added": False,
    "company_db_connection_added": False,
    "estimated_values_promoted": False,
}

source = evidence_bundle["source_assessment"]
assert source["source_role"] == "industry_platform_supplier_listing"
assert source["source_rank"] == "B"
assert source["currentness_status"] == "TARGET_PAGES_VISIBLE_2026-08-10"
assert "namespace-scoped" in " ".join(source["limitations"])

artifacts = {item["logical_ref"]: item for item in evidence_bundle["source_artifacts"]}
assert artifacts[
    "2026-06-23-gmai/outputs/mz100_supplier_yarns/cache/shop_6_yarn_page_1.html"
]["sha256"] == "e75d8867f1c69c35c47f3067231e9c5b10ff84505a12457b985fd808ed0db127"
assert artifacts[
    "2026-06-23-gmai/outputs/mz100_supplier_yarns/cache/shop_24_yarn_page_1.html"
]["sha256"] == "eac05c4a980ebf8d58814974e82c40158af273c4c08b1507b50e0cbe66d4e0bf"
assert artifacts[
    "2026-06-23-gmai/outputs/mz100_supplier_yarns/supplier_yarns.csv"
]["record_count"] == 51853

evidence = {item["evidence_id"]: item for item in evidence_bundle["evidence"]}
assert len(evidence) == 5
assert all(evidence_id.startswith("TMP-EV-") for evidence_id in evidence)
assert all(item["source_rank"] == "B" for item in evidence.values())

expected_evidence = {
    "TMP-EV-KC-20260810-MZ100-69586": (
        "https://www.mz100.cn/yarn/69586",
        "恒添纺织有限公司",
        "韩尚亚麻",
        "1/40NM",
        "10%亚麻 36%莱赛尔 40%腈纶 14%聚酯纤维",
    ),
    "TMP-EV-KC-20260810-MZ100-69587": (
        "https://www.mz100.cn/yarn/69587",
        "恒添纺织有限公司",
        "韩尚抗菌丝",
        "60NM/2 80NM/2",
        "60%人丝 40%精梳棉/45%人丝 55%精梳棉",
    ),
    "TMP-EV-KC-20260810-MZ100-52482": (
        "https://www.mz100.cn/yarn/52482",
        "宏森纺织品有限公司",
        "丝爽·云朵亚麻",
        "1/28NM",
        "85%天丝 5%亚麻 12%锦纶",
    ),
}
for evidence_id, expected in expected_evidence.items():
    item = evidence[evidence_id]
    observed = item["observed_fields"]
    actual = (
        item["source_url"],
        observed["listed_company"],
        observed["yarn_name"],
        observed["count_display"],
        observed["composition_raw"],
    )
    assert actual == expected

assert evidence["TMP-EV-KC-20260810-MZ100-69586"]["observed_fields"]["composition_total"] == 100
assert evidence["TMP-EV-KC-20260810-MZ100-69587"]["observed_fields"]["composition_variants_total"] == [100, 100]
assert evidence["TMP-EV-KC-20260810-MZ100-52482"]["evidence_status"] == "conflicting"
assert evidence["TMP-EV-KC-20260810-MZ100-52482"]["observed_fields"]["composition_total"] == 102

yue_tu_mao = [
    evidence["TMP-EV-KC-20260810-MZ100-65002"]["observed_fields"],
    evidence["TMP-EV-KC-20260810-MZ100-81858"]["observed_fields"],
]
assert all(row["yarn_name"] == "月兔毛" for row in yue_tu_mao)
assert {row["count_display"] for row in yue_tu_mao} == {"1/4.5NM", "1/12NM"}
assert {row["composition_raw"] for row in yue_tu_mao} == {
    "8%兔毛 81%尼龙 10%腈纶 1%氨纶",
    "32%Angora(兔毛)32%Wool(羊毛)33%Nylon(尼龙) 3%Spandex(氨纶)",
}

research = {item["research_id"]: item for item in evidence_bundle["research_records"]}
assert set(research) == {
    "TMP-RS-KC-20260810-MZ100-SOURCE",
    "TMP-RS-KC-20260810-YUETUMAO",
    "TMP-RS-KC-20260810-MZ100-69586",
    "TMP-RS-KC-20260810-MZ100-69587",
    "TMP-RS-KC-20260810-MZ100-52482",
}
assert all(item["reviewed_by"] is None and item["reviewed_at"] is None for item in research.values())
assert all(item["review_status"] in {"needs_more_evidence", "conflicting"} for item in research.values())
assert research["TMP-RS-KC-20260810-YUETUMAO"]["confidence"] == "high_for_non_uniqueness_only"
assert research["TMP-RS-KC-20260810-MZ100-52482"]["review_status"] == "conflicting"

assert intake["format"] == "KC_V04_INBOX_EXPORT"
assert intake["schema_version"] == "1.0"
assert intake["batch_id"] == "KC-MANUAL-20260810-BATCH3-MZ100"
items = intake["items"]
assert len(items) == 3
assert len({item["dedupe_key"] for item in items}) == 3
assert all(item["format"] == "KC_V04_INBOX_ITEM" for item in items)
assert all(item["review_status"] == "PENDING" for item in items)
assert all(item["payload"]["targetType"] == "yarn" for item in items)
assert all(item["payload"]["verificationStatus"] == "candidate" for item in items)
assert all(item["payload"]["sourceType"] == "industry_platform_supplier_listing" for item in items)
assert all(item["payload"]["targetId"].startswith("TMP-YN-") for item in items)
assert all(item["payload"]["commonIds"]["researchId"].startswith("TMP-RS-") for item in items)
assert all(item["payload"]["evidenceId"].startswith("TMP-EV-") for item in items)
assert all(item["payload"]["manufacturerName"] == "" for item in items)
assert all(item["payload"]["manufacturerId"] == "" for item in items)
assert all(item["payload"]["sellerName"] == item["payload"]["sourceOrganizationName"] for item in items)
assert all(item["payload"]["sellerId"] == item["payload"]["sourceOrganizationId"] for item in items)
assert all(item["payload"]["functionalProperties"] == [] for item in items)
assert all(item["payload"]["functionClaimStatus"] == "not_confirmed" for item in items)
assert all(item["payload"]["basicYarnForm"] == "unconfirmed" for item in items)
assert all(item["payload"]["yarnStructure"] == "" for item in items)
assert all(item["payload"]["spinningMethod"] == "" for item in items)
assert all(item["payload"]["gauge"] == "" for item in items)
assert all(item["payload"]["knittingEnds"] is None for item in items)
assert all(item["payload"]["yarnName"] != "月兔毛" for item in items)

by_code = {item["payload"]["yarnCode"]: item["payload"] for item in items}
assert set(by_code) == {"MZ100-69586", "MZ100-69587", "MZ100-52482"}

p69586 = by_code["MZ100-69586"]
assert p69586["countValue"] == "40" and p69586["plyCount"] == 1
assert p69586["compositionStatus"] == "candidate"
assert p69586["compositionTotal"] == percent_total(p69586["compositionRaw"]) == 100

p69587 = by_code["MZ100-69587"]
assert p69587["countValue"] == "" and p69587["plyCount"] is None
assert p69587["compositionTotal"] is None
assert p69587["fieldEvidence"]["countDisplay"]["status"] == "multiple_variants_unmapped"
assert p69587["fieldEvidence"]["compositionRaw"]["status"] == "multiple_variants_unmapped"
assert p69587["fieldEvidence"]["antibacterial"]["status"] == "name_only_not_confirmed"

p52482 = by_code["MZ100-52482"]
assert p52482["compositionStatus"] == "conflicting"
assert p52482["compositionTotal"] == percent_total(p52482["compositionRaw"]) == 102
assert p52482["fieldEvidence"]["tencelBrand"]["status"] == "not_confirmed_from_tiansi_wording"
assert "100%へ補正・正規化しない" in p52482["notes"]
assert "別名前空間" in p52482["notes"]

for payload in by_code.values():
    linked = evidence[payload["evidenceId"]]
    assert linked["source_url"] == payload["sourceUrl"]
    assert linked["target_id"] == payload["targetId"]

human_review = HUMAN_REVIEW_PATH.read_text(encoding="utf-8")
assert "normalizeStatus(payload?.[statusKey])==='confirmed'" in human_review
assert "compositionConfirmed?payload.compositionRaw:''" in human_review
assert "evidenceValue(payload.countValue,payload)" in human_review

print("mz100 research: OK (3 PENDING candidates, 5 evidence records, no master promotion, conflicts preserved)")
