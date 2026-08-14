#!/usr/bin/env python3
"""Validate the 2,000-record yarn catalog, intake surface, and market-signal overlay."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/yarn-catalog/mz100-catalog-2000.json"
EXPANDED_CATALOG = ROOT / "data/yarn-catalog/mz100-catalog-3000.json"
EXPANSION_STATUS = ROOT / "data/yarn-catalog/expansion-status.json"
PAGE = ROOT / "owner-yarns/index.html"
TOP_PAGE = ROOT / "brand-intelligence/index.html"
MARKET_SIGNALS = ROOT / "data/market-trends/market-signals.json"
MD_PROPOSALS = ROOT / "data/brand-md-monitoring/latest-material-proposals.json"
TRIAGE = ROOT / "data/human-review/2026-08-15-intake-19-triage.json"
MARKET_JS = ROOT / "market-signals.js"
BATCHES = [
    ROOT / "data/manual-intake/2026-08-08-weijie-hesheng-batch1.json",
    ROOT / "data/manual-intake/2026-08-08-weihai-yaxin-chengyun-batch2.json",
    ROOT / "data/manual-intake/2026-08-10-mz100-yarn-research-batch3.json",
    ROOT / "data/manual-intake/2026-08-12-twin-win-company-factory-batch4.json",
    ROOT / "data/manual-intake/2026-08-12-rope-picnic-gdm56050-batch5.json",
    ROOT / "data/manual-intake/2026-08-13-american-holic-products-batch6.json",
]

assert CATALOG.is_file(), "2,000-record catalog has not been generated"
data = json.loads(CATALOG.read_text(encoding="utf-8"))
records = data.get("records")
assert data.get("schema_version") == "1.0"
assert data.get("catalog_id") == "KC-YARN-CATALOG-MZ100-2000"
assert data.get("record_count") == 2000
assert isinstance(records, list) and len(records) == 2000
assert len({row.get("catalog_id") for row in records}) == 2000
assert len({row.get("source_url") for row in records}) == 2000
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
assert coverage["name"] == 2000
# Listing pages do not expose every field consistently. The quality floor verifies
# that each optional search facet is populated on a meaningful subset while all
# records retain a source ID and URL for detailed follow-up.
assert coverage["count_display"] >= 200
assert coverage["composition_raw"] >= 200
assert coverage["listed_supplier"] >= 200

expansion = json.loads(EXPANSION_STATUS.read_text(encoding="utf-8"))
assert expansion.get("format") == "KC_YARN_CATALOG_EXPANSION_STATUS"
assert expansion.get("current_searchable_count") == 2000
assert expansion.get("target_minimum_count", 0) >= 3000
assert expansion.get("target_policy") == "SEARCH_BASE_FIRST_DEEP_DIVE_ON_REQUEST_ONLY"
assert expansion.get("candidate_boundary", {}).get("master_status") == "NOT_PROMOTED"
assert expansion.get("candidate_boundary", {}).get("automatic_promotion") == "FORBIDDEN"
assert expansion.get("build", {}).get("target_output") == "data/yarn-catalog/mz100-catalog-3000.json"
if EXPANDED_CATALOG.is_file():
    expanded = json.loads(EXPANDED_CATALOG.read_text(encoding="utf-8"))
    expanded_records = expanded.get("records")
    assert expanded.get("record_count", 0) >= 3000
    assert isinstance(expanded_records, list) and len(expanded_records) >= 3000
    assert all(row.get("catalog_status") == "CATALOG_INDEXED" for row in expanded_records)
    assert all(row.get("verification_status") == "LISTING_PAGE_ONLY" for row in expanded_records)
    assert all(row.get("master_status") == "NOT_PROMOTED" for row in expanded_records)

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

assert len(all_items) == 19
assert len({item.get("dedupe_key") for item in all_items}) == 19
assert any(item.get("payload", {}).get("sourceOrganizationName", "").startswith("TWIN WIN") for item in all_items)
gdm = [item for item in all_items if item.get("payload", {}).get("productCode") == "GDM56050"]
assert len(gdm) == 1
assert gdm[0]["payload"]["productName"] == ""
assert gdm[0]["payload"]["compositionRaw"] == ""
assert gdm[0]["payload"]["verificationStatus"] == "candidate"
american_holic = [item for item in all_items if item.get("payload", {}).get("brandName") == "AMERICAN HOLIC"]
assert len(american_holic) == 2
assert {item["payload"].get("productCode") for item in american_holic} == {"0H001683000", "0H001978600"}
assert all(item["payload"].get("compositionStatus") == "confirmed" for item in american_holic)
cool_touch = next(item for item in american_holic if item["payload"].get("productCode") == "0H001683000")
assert any(prop.get("name") == "接触冷感" for prop in cool_touch["payload"].get("functionalProperties", []))

triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
assert triage.get("format") == "KC_HUMAN_REVIEW_TRIAGE"
assert triage.get("effect") == "ADVISORY_ONLY_NO_PROMOTION"
assert triage.get("source_review_status_required") == "PENDING"
decisions = triage.get("decisions")
assert isinstance(decisions, list) and len(decisions) == 19
assert {row.get("handoff_id") for row in decisions} == {item.get("handoff_id") for item in all_items}
assert {row.get("classification") for row in decisions} <= {"APPROVABLE", "CONDITIONAL", "HOLD"}
decision_counts = {label: sum(row.get("classification") == label for row in decisions) for label in ("APPROVABLE", "CONDITIONAL", "HOLD")}
assert decision_counts == {"APPROVABLE": 12, "CONDITIONAL": 4, "HOLD": 3}
assert triage.get("counts") == {**decision_counts, "AUTO_PROMOTED": 0}

md_proposals = json.loads(MD_PROPOSALS.read_text(encoding="utf-8"))
assert md_proposals.get("format") == "KC_BRAND64_MATERIAL_PROPOSALS"
assert md_proposals.get("observed_brand_count") == 64
assert md_proposals.get("sales_quantity_status") == "NOT_AVAILABLE"
assert md_proposals.get("sales_quantity_estimation") == "FORBIDDEN"
assert md_proposals.get("catalog_boundary") == "CATALOG_INDEXED / LISTING_PAGE_ONLY / NOT_PROMOTED"
assert md_proposals.get("publication_status") == "PUBLISH_HOLD"
assert len(md_proposals.get("proposals", [])) >= 3
assert all(row.get("status") == "MD_DRAFT" and row.get("publication_status") == "PUBLISH_HOLD" for row in md_proposals["proposals"])

html = PAGE.read_text(encoding="utf-8")
for required in (
    "mz100-catalog-2000.json",
    "kc_v04_handoff_queue_v1",
    "19件",
    "GDM56050",
    "TWIN WIN",
    "AMERICAN HOLIC",
    "2026-08-13-american-holic-products-batch6.json",
    "Human Review",
    "BACKUP_SHARE_ONLY",
    "Knit Compassを主系統",
    "TRIAGE_URL",
    "data/human-review/2026-08-15-intake-19-triage.json",
    "mz100-catalog-3000.json",
    "URLSearchParams(location.search)",
    "activateTab(location.hash.slice(1))",
    "market-signals.js",
):
    assert required in html, f"owner-yarns page missing: {required}"

top_html = TOP_PAGE.read_text(encoding="utf-8")
assert "market-signals.js" in top_html, "sales top is not connected to market signals"
assert "17件" not in top_html, "sales top still exposes the stale 17-candidate count"
for label in ("商品調査", "糸検索", "原料相場", "編み地イメージ", "生地検査", "Human Review", "19件"):
    assert label in top_html, f"sales navigation missing: {label}"
for stale_label in ("V04本体", "V04 TOP", "糸検索2,000件", "糸マスター2,000件", "v0.4受信箱"):
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
    f"(2000 catalog records, {len(analog_matches)} Analog Revival matches, "
    "19 PENDING candidates triaged 12/4/3, 3,000+ expansion queued, safety boundary preserved)"
)
