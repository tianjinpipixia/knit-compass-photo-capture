#!/usr/bin/env python3
"""Validate tiered Brand64 MD analysis and cross-brand interpretation rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_CONFIG = ROOT / "config/brand64-active-brands.json"
MONITORING_CONFIG = ROOT / "config/brand64-md-monitoring.json"
FRAMEWORK_CONFIG = ROOT / "config/brand-md-analysis-framework.json"
LATEST_WEEKLY = ROOT / "data/brand-md-monitoring/weekly/2026-08-24_2026-08-30-brand64-weekly-md.md"

EXPECTED_TIER_A = {
    "BR-00001": "UNIQLO",
    "BR-00002": "GU",
    "BR-00003": "MUJI",
    "BR-00004": "ROPÉ PICNIC",
    "BR-00006": "GLOBAL WORK",
    "BR-00012": "OPAQUE.CLIP",
    "BR-00047": "UNFILO",
    "BR-00051": "NATURAL BEAUTY BASIC",
    "BR-00054": "SLOBE IENA",
    "BR-00058": "Te chichi",
    "BR-00076": "SNIDEL",
}

REQUIRED_TIMELINE_FIELDS = {
    "first_seen_date",
    "preorder_start_date",
    "sales_start_date",
    "new_color_date",
    "restock_date",
    "promotion_push_date",
    "source_offline_date",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    active = load(ACTIVE_CONFIG)
    monitoring = load(MONITORING_CONFIG)
    framework = load(FRAMEWORK_CONFIG)

    assert framework.get("format") == "KC_BRAND_MD_ANALYSIS_FRAMEWORK"
    assert framework.get("active_brand_source") == "config/brand64-active-brands.json"
    assert framework.get("monitoring_source") == "config/brand64-md-monitoring.json"

    active_brands = active.get("active_brands", {})
    tier_a = framework.get("scan_strategy", {}).get("tier_a_deep_dive", {})
    tier_a_brands = tier_a.get("brands", {})
    assert tier_a.get("mode") == "FULL_MD_TIMELINE"
    assert tier_a.get("brand_count") == 11 == len(tier_a_brands)
    assert tier_a_brands == EXPECTED_TIER_A
    for brand_id, brand_name in EXPECTED_TIER_A.items():
        assert active_brands.get(brand_id) == brand_name

    default_scan = framework.get("scan_strategy", {}).get("brand64_default", {})
    assert default_scan.get("mode") == "DIFF_ONLY_WITH_ESCALATION"
    assert default_scan.get("escalation_action") == "TEMPORARY_DEEP_DIVE"
    assert default_scan.get("escalation_triggers")

    timeline = framework.get("product_timeline", {})
    assert REQUIRED_TIMELINE_FIELDS <= set(timeline.get("required_when_available", []))
    timeline_rules = timeline.get("rules", {})
    assert timeline_rules.get("prefer_explicit_sales_start") is True
    assert timeline_rules.get("first_seen_is_not_sales_start") is True
    assert timeline_rules.get("inferred_dates_must_be_labeled") is True
    assert "AUTHORIZED_RETAILER_EXPLICIT_DATE" in timeline.get("sales_start_evidence_levels", [])

    relationship = framework.get("cross_brand_relationships", {}).get("fast_retailing_trend_to_life", {})
    assert relationship.get("relationship_type") == "TREND_TO_LIFE_TRANSLATION"
    assert relationship.get("model_status") == "OWNER_DOMAIN_MODEL"
    assert relationship.get("not_an_official_corporate_claim") is True
    trend = relationship.get("trend_signal_brand", {})
    life = relationship.get("life_translation_brand", {})
    assert trend.get("brand_id") == "BR-00002"
    assert trend.get("brand_name") == "GU"
    assert trend.get("role") == "TREND"
    assert life.get("brand_id") == "BR-00001"
    assert life.get("brand_name") == "UNIQLO"
    assert life.get("role") == "LIFE"
    assert "launch_lag_days_when_dates_are_confirmed" in relationship.get("derived_outputs", [])
    assert "Do not label similarity as copying" in relationship.get("interpretation_rule", "")

    monthly_outputs = set(framework.get("monthly_md_outputs", []))
    for required in {
        "brand_month_timeline",
        "carryover_vs_new_structure",
        "capsule_structure",
        "sleeve_length_transition",
        "color_transition",
        "function_persistence",
        "cross_brand_relationship_findings",
    }:
        assert required in monthly_outputs

    assert monitoring.get("analysis_framework_source") == "config/brand-md-analysis-framework.json"
    monitoring_tier_ids = monitoring.get("tiered_analysis", {}).get("tier_a_deep_dive_brand_ids", [])
    assert monitoring_tier_ids == list(EXPECTED_TIER_A)
    assert monitoring.get("tiered_analysis", {}).get("other_brand64_mode") == "DIFF_ONLY_WITH_ESCALATION"
    assert monitoring.get("tiered_analysis", {}).get("ui_change") == "NONE"

    daily = monitoring.get("cadence", {}).get("daily", {})
    assert REQUIRED_TIMELINE_FIELDS <= set(daily.get("tier_a_timeline_fields", []))
    assert daily.get("sales_start_date_rule") == "NEVER_EQUATE_FIRST_SEEN_WITH_SALES_START_WITHOUT_EVIDENCE"
    rules = monitoring.get("rules", {})
    assert rules.get("preserve_sales_start_separately_from_first_seen") is True
    assert rules.get("preserve_new_color_and_promotion_dates") is True
    assert rules.get("cross_brand_similarity_is_not_copying_claim") is True

    weekly = monitoring.get("cadence", {}).get("weekly", {})
    canonical = weekly.get("canonical_storage", {})
    assert weekly.get("display_language") == "ja-JP"
    assert weekly.get("language_policy") == "WEEKLY_SUMMARY_AND_MD_IMPLICATIONS_MUST_BE_WRITTEN_IN_PLAIN_JAPANESE"
    assert canonical.get("public_surface_policy") == "OWNER_REVIEW_ONLY_UNTIL_HUMAN_APPROVAL"

    latest_weekly = LATEST_WEEKLY.read_text(encoding="utf-8")
    for heading in ["## 週次MDのまとめ", "### 確認できた事実", "### MDへの示唆", "## 素材開発の優先テーマ", "## 次週の重点確認事項"]:
        assert heading in latest_weekly

    print(
        "brand MD analysis framework: OK "
        "(11 Tier-A brands, Brand64 diff escalation, GU=TREND, UNIQLO=LIFE, explicit launch timeline)"
    )


if __name__ == "__main__":
    main()
