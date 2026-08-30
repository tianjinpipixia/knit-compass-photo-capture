#!/usr/bin/env python3
"""Validate the active 3,000-record yarn catalog and its safety boundaries."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FALLBACK_CATALOG = ROOT / "data/yarn-catalog/mz100-catalog-2000.json"
CATALOG = ROOT / "data/yarn-catalog/mz100-catalog-3000.json"
EXPANSION_STATUS = ROOT / "data/yarn-catalog/expansion-status.json"
PAGE = ROOT / "owner-yarns/index.html"
TOP_PAGE = ROOT / "brand-intelligence/index.html"
MARKET_SIGNALS = ROOT / "data/market-trends/market-signals.json"
MD_PROPOSALS = ROOT / "data/brand-md-monitoring/latest-material-proposals.json"
TRIAGE = ROOT / "data/human-review/2026-08-18-intake-24-triage.json"
MARKET_JS = ROOT / "market-signals.js"
BATCHES = [
    ROOT / "data/manual-intake/2026-08-08-weijie-hesheng-batch1.json",
    ROOT / "data/manual-intake/2026-08-08-weihai-yaxin-chengyun-batch2.json",
    ROOT / "data/manual-intake/2026-08-10-mz100-yarn-research-batch3.json",
    ROOT / "data/manual-intake/2026-08-12-twin-win-company-factory-batch4.json",
    ROOT / "data/manual-intake/2026-08-12-rope-picnic-gdm56050-batch5.json",
    ROOT / "data/manual-intake/2026-08-13-american-holic-products-batch6.json",
    ROOT / "data/manual-intake/2026-08-17-minghai-wool-silk-core-spun-batch7.json",
    ROOT / "data/manual-intake/2026-08-18-american-holic-products-batch8.json",
    ROOT / "data/manual-intake/2026-08-18-dinghong-mz100-25139-batch9.json",
]

assert FALLBACK_CATALOG.is_file(), "2,000-record fallback catalog is missing"
fallback = json.loads(FALLBACK_CATALOG.read_text(encoding="utf-8"))
assert fallback.get("record_count") == 2000
assert isinstance(fallback.get("records"), list) and len(fallback["records"]) == 2000
assert all(row.get("master_status") == "NOT_PROMOTED" for row in fallback["records"])

assert CATALOG.is_file(), "3,000-record active catalog has not been generated"
data = json.loads(CATALOG.read_text(encoding="utf-8"))
records = data.get("records")
assert data.get("schema_version") == "1.0"
assert data.get("catalog_id") == "KC-YARN-CATALOG-MZ100-3000"
assert data.get("record_count") == 3000
assert isinstance(records, list) and len(records) == 3000
assert len({row.get("catalog_id") for row in records}) == 3000
assert len({row.get("source_url") for row in records}) == 3000
assert all(row.get("source") == "MZ100" for row in records)
assert all(row.get("catalog_status") == "CATALOG_INDEXED" for row in records)
assert all(row.get("verification_status") == "LISTING_PAGE_ONLY" for row in records)
assert all(row.get("master_status") == "NOT_PROMOTED" for row in records)
assert all(re.fullmatch(r"https://www\.mz100\.cn/yarn/\d+", row.get("source_url", "")) for row in records)

coverage = {
    "name": sum(bool(str(row.get("name") or "").strip()) for row in records),
    "count_display": sum(bool(str(row.get("count_display") or "").strip()) for row in records),
    "composition_raw": sum(bool(str(row.get("composition_raw") or "").strip()) for row in records),
    "listed_supplier": sum(bool(str(row.get("listed_supplier") or "").strip()) for row in records),
}
print("catalog field coverage:", coverage)
assert coverage["name"] == 3000
assert coverage["count_display"] >= 200
assert coverage["composition_raw"] >= 200
assert coverage["listed_supplier"] >= 200

expansion = json.loads(EXPANSION_STATUS.read_text(encoding="utf-8"))
assert expansion.get("format") == "KC_YARN_CATALOG_EXPANSION_STATUS"
assert expansion.get("current_searchable_count") == 3000
assert expansion.get("target_minimum_count", 0) >= 3000
assert expansion.get("target_policy") == "SEARCH_BASE_FIRST_DEEP_DIVE_ON_REQUEST_ONLY"
assert expansion.get("candidate_boundary", {}).get("master_status") == "NOT_PROMOTED"
assert expansion.get("candidate_boundary", {}).get("automatic_promotion") == "FORBIDDEN"
assert expansion.get("build", {}).get("target_output") == "data/yarn-catalog/mz100-catalog-3000.json"
assert expansion.get("build", {}).get("status") == "SUCCESS"
assert expansion.get("publication_status") == "ACTIVE"

assert MARKET_SIGNALS.is_file(), "market signal registry is missing"
signal_data = json.loads(MARKET_SIGNALS.read_text(encoding="utf-8"))
assert signal_data.get("format") == "KC_MARKET_SIGNALS"
assert signal_data.get("schema_version") == "1.0"
signals = signal_data.get("signals")
assert isinstance(signals, list) and signals
analog = next((signal for signal in signals if signal.get("id") == "analog-revival"), None)
assert analog, "Analog Revival signal is missing"
assert analog.get("name_ja") == "アナログ回帰"
assert analog.get("name_en") == "Analog Revival"
assert analog.get("status") == "ACTIVE_SIGNAL"
assert analog.get("source", {}).get("publisher") == "VOGUE JAPAN"
assert analog.get("source", {}).get("url") == "https://www.vogue.co.jp/article/genz-analog-revival"
assert analog.get("consumer_insight")
assert analog.get("recommended_yarn_types")
assert analog.get("recommended_knits")
assert analog.get("match_rules")

terms = [
    str(term).lower()
    for rule in analog.get("match_rules", [])
    for term in rule.get("terms", [])
    if str(term).strip()
]
analog_matches = []
for row in records:
    hay = " ".join(
        str(row.get(field) or "")
        for field in ("name", "count_display", "composition_raw", "listed_supplier", "source_id")
    ).lower()
    if any(term in hay for term in terms):
        analog_matches.append(row)
assert analog_matches, "Analog Revival rules do not match any catalog yarns"
print("Analog Revival catalog matches:", len(analog_matches))

all_items = []
for path in BATCHES:
    assert path.is_file(), f"missing batch: {path.name}"
    batch = json.loads(path.read_text(encoding="utf-8"))
    assert batch.get("format") == "KC_V04_INBOX_EXPORT"
    assert isinstance(batch.get("items"), list) and batch["items"]
    assert all(item.get("review_status") == "PENDING" for item in batch["items"])
    all_items.extend(batch["items"])

assert len(all_items) == 24
assert len({item.get("dedupe_key") for item in all_items}) == 24
assert any(item.get("payload", {}).get("sourceOrganizationName", "").startswith("TWIN WIN") for item in all_items)
gdm = [item for item in all_items if item.get("payload", {}).get("productCode") == "GDM56050"]
assert len(gdm) == 1
assert gdm[0]["payload"]["productName"] == ""
assert gdm[0]["payload"]["compositionRaw"] == ""
assert gdm[0]["payload"]["verificationStatus"] == "candidate"
american_holic = [item for item in all_items if item.get("payload", {}).get("brandName") == "AMERICAN HOLIC"]
assert len(american_holic) == 4
assert {item["payload"].get("productCode") for item in american_holic} == {
    "0H001683000",
    "0H001978600",
    "0H001683100",
    "0H002151200",
}
assert all(item["payload"].get("compositionStatus") == "confirmed" for item in american_holic)
minghai = [item for item in all_items if item.get("handoff_id") == "HF-MANUAL-20260817-20-MINGHAI-WOOL-SILK-2-50"]
assert len(minghai) == 1
minghai_payload = minghai[0]["payload"]
assert minghai_payload.get("yarnName") == "羊毛绢丝包芯纱"
assert minghai_payload.get("countDisplay") == "2/50NM"
assert minghai_payload.get("basicYarnForm") == "core_spun"
assert minghai_payload.get("compositionRaw") == "15% wool / 5% silk / 32% lyocell / 20% nylon / 28% PBT"
assert minghai_payload.get("compositionTotal") == 100
assert minghai_payload.get("manufacturerName") == ""
assert minghai_payload.get("sourceUrl") == ""
assert minghai_payload.get("verificationStatus") == "candidate"
assert "QUEEN" not in json.dumps(minghai_payload, ensure_ascii=False)

dinghong_org = [item for item in all_items if item.get("handoff_id") == "HF-MANUAL-20260818-23-DINGHONG"]
assert len(dinghong_org) == 1
dinghong_org_payload = dinghong_org[0]["payload"]
assert dinghong_org_payload.get("targetType") == "organization"
assert dinghong_org_payload.get("targetId") == "TMP-OR-KC-20260818-DINGHONG"
assert dinghong_org_payload.get("sourceOrganizationName") == "东莞市鼎宏纺织品有限公司"
assert dinghong_org_payload.get("manufacturerName") == ""
assert dinghong_org_payload.get("organizationProfile", {}).get("legalNameEnglish") == "Dongguan Dinghong Textile Co Ltd"
assert "东莞市鼎宏纺织有限公司" in dinghong_org_payload.get("organizationProfile", {}).get("aliases", [])

dinghong_yarn = [item for item in all_items if item.get("handoff_id") == "HF-MANUAL-20260818-24-MZ100-25139"]
assert len(dinghong_yarn) == 1
dinghong_yarn_payload = dinghong_yarn[0]["payload"]
assert dinghong_yarn_payload.get("targetType") == "yarn"
assert dinghong_yarn_payload.get("yarnName") == "羊毛马海毛"
assert dinghong_yarn_payload.get("yarnCode") == "MZ100-25139"
assert dinghong_yarn_payload.get("countSystem") == "unknown"
assert dinghong_yarn_payload.get("countDisplay") == "9S/1 13S/1"
assert dinghong_yarn_payload.get("compositionRaw") == "8%马海毛 30%尼龙(锦纶) 15%羊毛 47%腈纶"
assert dinghong_yarn_payload.get("compositionTotal") == 100
assert dinghong_yarn_payload.get("manufacturerName") == ""
assert dinghong_yarn_payload.get("sourceUrl") == "https://www.mz100.cn/seka/25139"
assert dinghong_yarn_payload.get("verificationStatus") == "candidate"
assert dinghong_yarn_payload.get("fieldEvidence", {}).get("countDisplay", {}).get("status") == "raw_text_count_system_unconfirmed"

cool_touch = next(item for item in american_holic if item["payload"].get("productCode") == "0H001683000")
assert any(prop.get("name") == "接触冷感" for prop in cool_touch["payload"].get("functionalProperties", []))

uv_cardigan = next(item for item in american_holic if item["payload"].get("productCode") == "0H001683100")
uv_payload = uv_cardigan["payload"]
assert uv_payload.get("compositionRaw") == "綿74% / ナイロン26%"
assert uv_payload.get("countryOfOrigin") == "Bangladesh"
assert uv_payload.get("verificationStatus") == "owner_observed"
assert any(prop.get("code") == "UV_CUT" for prop in uv_payload.get("functionalProperties", []))
assert all(not prop.get("test") for prop in uv_payload.get("functionalProperties", []))

shaggy_vest = next(item for item in american_holic if item["payload"].get("productCode") == "0H002151200")
shaggy_payload = shaggy_vest["payload"]
assert shaggy_payload.get("compositionRaw") == "ナイロン100%"
assert shaggy_payload.get("countryOfOrigin") == "China"
assert shaggy_payload.get("verificationStatus") == "owner_observed"
assert any(prop.get("code") == "COOL_TOUCH" for prop in shaggy_payload.get("functionalProperties", []))
assert all(not prop.get("test") for prop in shaggy_payload.get("functionalProperties", []))
assert shaggy_payload.get("fieldEvidence", {}).get("yarnStructure", {}).get("status") == "not_confirmed_do_not_promote"

triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
assert triage.get("format") == "KC_HUMAN_REVIEW_TRIAGE"
assert triage.get("effect") == "ADVISORY_ONLY_NO_PROMOTION"
assert triage.get("source_review_status_required") == "PENDING"
decisions = triage.get("decisions")
assert isinstance(decisions, list) and len(decisions) == 24
assert {row.get("handoff_id") for row in decisions} == {item.get("handoff_id") for item in all_items}
assert {row.get("classification") for row in decisions} <= {"APPROVABLE", "CONDITIONAL", "HOLD"}
decision_counts = {label: sum(row.get("classification") == label for row in decisions) for label in ("APPROVABLE", "CONDITIONAL", "HOLD")}
assert decision_counts == {"APPROVABLE": 14, "CONDITIONAL": 7, "HOLD": 3}
assert triage.get("counts") == {**decision_counts, "AUTO_PROMOTED": 0}

md_proposals = json.loads(MD_PROPOSALS.read_text(encoding="utf-8"))
assert md_proposals.get("format") == "KC_BRAND64_MATERIAL_PROPOSALS"
assert md_proposals.get("observed_brand_count") == 64
assert md_proposals.get("sales_quantity_status") == "NOT_AVAILABLE"
assert md_proposals.get("sales_quantity_estimation") == "FORBIDDEN"
assert md_proposals.get("catalog_boundary") == (
    "OFFICIAL_INDIVIDUAL_PRODUCT_PAGE_REQUIRED_FOR_FORMAL_CANDIDATE / "
    "LISTING_AND_NEWS_SIGNALS_REMAIN_OBSERVATION_ONLY"
)
assert md_proposals.get("publication_status") == "PUBLISH_HOLD"
assert len(md_proposals.get("proposals", [])) >= 3
assert all(
    row.get("status") in {"MD_DRAFT", "OPERATIONAL_DRAFT"}
    and row.get("publication_status") == "PUBLISH_HOLD"
    for row in md_proposals["proposals"]
)

html = PAGE.read_text(encoding="utf-8")
for required in (
    "mz100-catalog-2000.json",
    "kc_v04_handoff_queue_v1",
    "24件",
    "GDM56050",
    "TWIN WIN",
    "AMERICAN HOLIC",
    "鼎宏",
    "MZ100 25139",
    "2026-08-13-american-holic-products-batch6.json",
    "2026-08-18-american-holic-products-batch8.json",
    "2026-08-18-dinghong-mz100-25139-batch9.json",
    "Human Review",
    "BACKUP_SHARE_ONLY",
    "Knit Compassを主系統",
    "TRIAGE_URL",
    "data/human-review/2026-08-18-intake-24-triage.json",
    "mz100-catalog-3000.json",
    "URLSearchParams(location.search)",
    "activateTab(location.hash.slice(1))",
    "market-signals.js",
):
    assert required in html, f"owner-yarns page missing: {required}"

top_html = TOP_PAGE.read_text(encoding="utf-8")
assert "market-signals.js" in top_html, "sales top is not connected to market signals"
assert "17件" not in top_html, "sales top still exposes the stale 17-candidate count"
for label in ("商品調査", "糸検索", "原料相場", "編み地イメージ", "生地検査", "Human Review", "24件"):
    assert label in top_html, f"sales navigation missing: {label}"
for stale_label in ("V04本体", "V04 TOP", "糸検索2,000件", "糸マスター2,000件", "v0.4受信箱", "未反映22件"):
    assert stale_label not in top_html, f"sales top exposes stale label: {stale_label}"

market_js = MARKET_JS.read_text(encoding="utf-8")
for required in (
    "MARKET SIGNALS / 市場トレンド",
    "analog-revival",
    "kcTrendFilter",
    "market_trend_tags",
    "関連素材を見る",
    "VOGUE記事",
    "元カタログの事実データは変更せず",
):
    assert required in market_js, f"market signal UI missing: {required}"

print(
    "owner yarn implementation: OK "
    f"(3000 active catalog records, {len(analog_matches)} Analog Revival matches, "
    "24 PENDING candidates triaged 14/7/3, zero automatic promotion, safety boundary preserved)"
)
