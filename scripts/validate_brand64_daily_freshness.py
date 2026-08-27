#!/usr/bin/env python3
"""Validate the latest active 64-brand daily observation and freshness rules."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "data/brand-md-monitoring/latest.json"
PROPOSALS = ROOT / "data/brand-md-monitoring/latest-material-proposals.json"
ACTIVE_CONFIG = ROOT / "config/brand64-active-brands.json"
MONITORING_CONFIG = ROOT / "config/brand64-md-monitoring.json"
EXTERNAL_CONFIG = ROOT / "config/md-external-signal-brands.json"
ZARA_BASELINE = ROOT / "data/brand-md-monitoring/2026-08-19-zara-initial-baseline.jsonl"
SNIDEL_BASELINE = ROOT / "data/brand-md-monitoring/2026-08-19-snidel-initial-baseline.jsonl"
EXPECTED_PAL_IDS = {f"BR-{i:05d}" for i in range(65, 75)}
EXPECTED_ZARA_ID = "BR-00075"
EXPECTED_SNIDEL_ID = "BR-00076"
EXPECTED_INACTIVE_IDS = {
    "BR-00020", "BR-00026", "BR-00029", "BR-00034", "BR-00037", "BR-00038",
    "BR-00043", "BR-00044", "BR-00045", "BR-00046", "BR-00048", "BR-00061",
}
EXPECTED_EXTERNAL_NAMES = {
    "PLST", "FRAY I.D", "H&M", "COS", "MANGO", "NOLLEY'S", "BEAUTY&YOUTH"
}


def repository_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    path.relative_to(ROOT.resolve())
    return path


def valid_http_url(value: str) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_daily_snapshot(path: Path) -> tuple[str, dict | list[dict]]:
    """Support both legacy 64-row JSONL and the structured daily-observation JSON."""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return "rows", []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return "rows", load_jsonl(path)
    if isinstance(parsed, dict) and parsed.get("format") == "KC_BRAND64_DAILY_OBSERVATION":
        return "structured", parsed
    if isinstance(parsed, list):
        return "rows", parsed
    return "rows", load_jsonl(path)


def row_id(row: dict) -> str:
    return str(row.get("id") or row.get("brand_id") or "")


def row_name(row: dict) -> str:
    return str(row.get("b") or row.get("brand") or row.get("brand_name") or "")


def validate_single_baseline(path: Path, expected_id: str, expected_name: str) -> None:
    assert path.is_file()
    rows = load_jsonl(path)
    assert len(rows) == 1
    row = rows[0]
    assert row_id(row) == expected_id
    assert row_name(row) == expected_name
    assert row.get("d") == "2026-08-19"
    assert valid_http_url(row.get("u"))
    assert row.get("q") in {"NA", "NOT_AVAILABLE"}
    assert row.get("p") in {"HOLD", "PUBLISH_HOLD"}


def validate_structured_daily(
    daily: dict,
    latest: dict,
    active_brands: dict[str, str],
    inactive_brands: dict[str, str],
) -> None:
    assert daily.get("format") == "KC_BRAND64_DAILY_OBSERVATION"
    assert daily.get("observed_date") == latest["observed_date"]
    assert daily.get("active_brand_source") == latest["active_brand_source"]
    assert daily.get("active_brand_count") == 64

    checked_ids = daily.get("checked_brand_ids", [])
    assert len(checked_ids) == 64
    assert len(set(checked_ids)) == 64
    assert set(checked_ids) == set(active_brands)
    light_count = daily.get("light_check_count", daily.get("light_check_completed"))
    assert light_count == 64

    deep_ids = daily.get("deep_dive_brand_ids", [])
    assert len(deep_ids) == daily.get("deep_dive_brand_count", daily.get("deep_dive_completed", len(deep_ids)))
    assert set(deep_ids) <= set(active_brands)

    assert daily.get("sales_quantity_policy") == "NO_ESTIMATION"
    assert daily.get("publication_status") == "PUBLISH_HOLD"
    assert daily.get("human_review_required") is True

    for item in daily.get("status_overrides", []):
        if isinstance(item, dict) and item.get("official_url"):
            assert valid_http_url(item["official_url"])
            assert item.get("brand_id") in active_brands
            if item.get("brand_name"):
                assert item["brand_name"] == active_brands[item["brand_id"]]

    details = daily.get("meaningful_delta_details", {})
    if isinstance(details, dict):
        for brand_id, item in details.items():
            assert brand_id in active_brands
            if isinstance(item, dict) and item.get("official_url"):
                assert valid_http_url(item["official_url"])

    inactive_path = repository_path(latest["inactive_legacy_reference_path"])
    assert inactive_path.is_file()
    inactive_rows = load_jsonl(inactive_path)
    assert len(inactive_rows) == len(inactive_brands)
    assert {row_id(row) for row in inactive_rows} == set(inactive_brands)
    for row in inactive_rows:
        assert row_name(row) == inactive_brands[row_id(row)]
        assert row.get("observed_date") == latest["observed_date"]
        assert row.get("included_in_active_aggregation") is False
        assert row.get("history_preserved") is True

    product_path = latest.get("product_baseline_path")
    if product_path:
        assert repository_path(product_path).is_file()
    risk_path = latest.get("product_risk_path")
    if risk_path:
        assert repository_path(risk_path).is_file()

    if daily.get("observed_at") is None:
        assert daily.get("observation_mode") == "RETROSPECTIVE_GAP_RECOVERY"
        assert daily.get("recovered_on")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-age-days", type=int)
    args = parser.parse_args()

    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    proposals = json.loads(PROPOSALS.read_text(encoding="utf-8"))
    active_config = json.loads(ACTIVE_CONFIG.read_text(encoding="utf-8"))
    monitoring_config = json.loads(MONITORING_CONFIG.read_text(encoding="utf-8"))
    external_config = json.loads(EXTERNAL_CONFIG.read_text(encoding="utf-8"))
    observed_date = date.fromisoformat(latest["observed_date"])

    assert active_config.get("format") == "KC_BRAND64_ACTIVE_SET"
    active_brands = active_config.get("active_brands", {})
    inactive_brands = active_config.get("inactive_legacy_brands", {})
    assert active_config.get("active_brand_count") == 64 == len(active_brands)
    assert active_config.get("inactive_legacy_count") == len(EXPECTED_INACTIVE_IDS) == len(inactive_brands)
    assert len(set(active_brands.values())) == 64
    assert len(set(inactive_brands.values())) == len(EXPECTED_INACTIVE_IDS)
    assert not (set(active_brands) & set(inactive_brands))
    assert set(inactive_brands) == EXPECTED_INACTIVE_IDS
    assert EXPECTED_PAL_IDS <= set(active_brands)
    assert active_brands.get(EXPECTED_ZARA_ID) == "ZARA"
    assert active_brands.get(EXPECTED_SNIDEL_ID) == "SNIDEL"
    assert inactive_brands.get("BR-00048") == "TAKEO KIKUCHI"
    assert inactive_brands.get("BR-00020") == "any FAM"
    assert active_config.get("inactive_policy", {}).get("brand_id_reuse") == "FORBIDDEN"
    assert active_config.get("inactive_policy", {}).get("history_preserved") is True

    pal = active_config.get("pal_group", {})
    assert valid_http_url(pal.get("common_knit_entry_url"))
    pal_brands = pal.get("brands", {})
    assert set(pal_brands) == EXPECTED_PAL_IDS
    for brand_id, item in pal_brands.items():
        assert item.get("brand_name") == active_brands[brand_id]
        assert valid_http_url(item.get("official_url"))
        assert "palcloset.jp" in item.get("official_url", "")

    global_signals = active_config.get("global_signal_brands", {})
    zara = global_signals.get(EXPECTED_ZARA_ID, {})
    assert zara.get("brand_name") == "ZARA"
    assert zara.get("role") == "GLOBAL_FAST_FASHION_LEADING_MD_SIGNAL"
    assert valid_http_url(zara.get("official_url"))
    assert valid_http_url(zara.get("special_prices_url"))
    assert "zara.com" in zara.get("official_url", "")
    validate_single_baseline(ZARA_BASELINE, EXPECTED_ZARA_ID, "ZARA")

    japan_signals = active_config.get("japan_signal_brands", {})
    snidel = japan_signals.get(EXPECTED_SNIDEL_ID, {})
    assert snidel.get("brand_name") == "SNIDEL"
    assert snidel.get("role") == "JAPAN_FEMININE_DESIGN_FUNCTION_LEADING_MD_SIGNAL"
    for key in ("official_url", "knit_url", "cardigan_url"):
        assert valid_http_url(snidel.get(key))
        assert "usagi-online.com" in snidel.get(key, "")
    validate_single_baseline(SNIDEL_BASELINE, EXPECTED_SNIDEL_ID, "SNIDEL")

    assert external_config.get("format") == "KC_MD_EXTERNAL_SIGNAL_SET"
    external_brands = external_config.get("brands", {})
    assert external_config.get("brand_count") == 7 == len(external_brands)
    assert {item.get("brand_name") for item in external_brands.values()} == EXPECTED_EXTERNAL_NAMES
    assert external_config.get("rules", {}).get("brand64_membership") == "OUTSIDE_BRAND64"
    assert external_config.get("rules", {}).get("sales_quantity_estimation") == "FORBIDDEN"
    assert external_config.get("rules", {}).get("publication_status") == "PUBLISH_HOLD"
    assert not (EXPECTED_EXTERNAL_NAMES & set(active_brands.values()))
    for signal_id, item in external_brands.items():
        assert signal_id.startswith("EXT-MD-")
        assert valid_http_url(item.get("official_url"))
        assert item.get("weekly_checks")

    assert monitoring_config.get("format") == "KC_BRAND64_MD_MONITORING"
    assert monitoring_config.get("active_brand_count") == 64
    assert monitoring_config.get("external_signal_source") == "config/md-external-signal-brands.json"
    assert monitoring_config.get("external_signal_brand_count") == 7
    assert monitoring_config.get("japan_signal_group", {}).get("brands") == [EXPECTED_SNIDEL_ID]
    assert monitoring_config.get("global_signal_group", {}).get("brands") == [EXPECTED_ZARA_ID]
    assert monitoring_config.get("rules", {}).get("external_signals_do_not_change_brand64_count") is True

    transition = active_config.get("transition", {})
    effective_from = date.fromisoformat(transition.get("effective_from"))
    removed_from_active = transition.get("removed_from_active", {})
    added_to_active = transition.get("added_to_active", {})
    assert removed_from_active == {
        "BR-00020": "any FAM",
        "BR-00048": "TAKEO KIKUCHI",
    }
    assert added_to_active == {
        "BR-00075": "ZARA",
        "BR-00076": "SNIDEL",
    }

    snapshot_active_brands = dict(active_brands)
    snapshot_inactive_ids = set(inactive_brands)
    if observed_date < effective_from:
        for brand_id in added_to_active:
            snapshot_active_brands.pop(brand_id, None)
        for brand_id, brand_name in removed_from_active.items():
            snapshot_active_brands[brand_id] = brand_name
        snapshot_inactive_ids -= set(removed_from_active)
    assert len(snapshot_active_brands) == 64

    assert latest.get("format") == "KC_BRAND64_MD_LATEST_POINTER"
    assert latest.get("active_brand_source") == "config/brand64-active-brands.json"
    assert latest.get("sales_quantity_policy") == "NO_ESTIMATION"
    assert latest.get("publication_status") == "PUBLISH_HOLD"
    assert proposals.get("format") == "KC_BRAND64_MATERIAL_PROPOSALS"
    assert proposals.get("observed_date") == latest.get("observed_date")
    assert proposals.get("observed_brand_count") == 64
    assert proposals.get("active_brand_source") == latest.get("active_brand_source")
    assert proposals.get("sales_quantity_status") == "NOT_AVAILABLE"
    assert proposals.get("sales_quantity_estimation") == "FORBIDDEN"
    assert proposals.get("publication_status") == "PUBLISH_HOLD"
    assert all(
        row.get("status") in {"MD_DRAFT", "OPERATIONAL_DRAFT"}
        for row in proposals.get("proposals", [])
    )
    assert all(row.get("publication_status") == "PUBLISH_HOLD" for row in proposals.get("proposals", []))

    daily_path = repository_path(latest["daily_path"])
    summary_path = repository_path(latest["summary_path"])
    assert daily_path.is_file()
    assert summary_path.is_file()
    assert proposals.get("source_daily_path") == latest.get("daily_path")
    assert proposals.get("source_summary_path") == latest.get("summary_path")
    assert latest.get("active_daily_overlay_paths", []) == proposals.get("active_daily_overlay_paths", [])

    daily_mode, daily_payload = load_daily_snapshot(daily_path)
    if daily_mode == "structured":
        assert isinstance(daily_payload, dict)
        validate_structured_daily(daily_payload, latest, snapshot_active_brands, inactive_brands)
    else:
        assert isinstance(daily_payload, list)
        primary_rows = daily_payload
        overlay_paths = [repository_path(p) for p in latest.get("active_daily_overlay_paths", [])]
        overlay_rows = []
        for path in overlay_paths:
            assert path.is_file()
            overlay_rows.extend(load_jsonl(path))

        all_rows = primary_rows + overlay_rows
        active_rows = [row for row in all_rows if row_id(row) in snapshot_active_brands]
        active_ids = [row_id(row) for row in active_rows]
        assert len(active_rows) == 64
        assert len(set(active_ids)) == 64
        assert set(active_ids) == set(snapshot_active_brands)
        for row in active_rows:
            brand_id = row_id(row)
            assert row_name(row) == snapshot_active_brands[brand_id]
            assert (row.get("d") or row.get("observed_date")) == latest["observed_date"]
            assert valid_http_url(row.get("u") or row.get("source"))
            assert (row.get("q") or row.get("sales_quantity_status")) in {"NA", "NOT_AVAILABLE"}
            assert (row.get("p") or row.get("publication_status")) in {"HOLD", "PUBLISH_HOLD"}

        if observed_date < effective_from:
            legacy_present = {row_id(row) for row in primary_rows if row_id(row) in snapshot_inactive_ids}
            assert legacy_present == snapshot_inactive_ids
            assert set(removed_from_active) <= set(active_ids)
            assert not (set(added_to_active) & set(active_ids))
        else:
            assert not (set(removed_from_active) & set(active_ids))
            assert set(added_to_active) <= set(active_ids)

        pal_active_rows = [row for row in active_rows if row_id(row) in EXPECTED_PAL_IDS]
        assert len(pal_active_rows) == 10
        assert all("palcloset.jp" in (row.get("u") or "") for row in pal_active_rows)

    previous_daily = latest.get("previous_daily_path")
    if previous_daily:
        assert repository_path(previous_daily).is_file()

    if args.max_age_days is not None:
        age_days = (date.today() - observed_date).days
        assert age_days <= args.max_age_days, (
            f"brand64 daily observation is stale: observed={observed_date}, age_days={age_days}, "
            f"allowed={args.max_age_days}"
        )

    current_or_transition = "current" if observed_date >= effective_from else "pre-transition snapshot"
    print(
        f"brand64 active daily freshness: OK ({latest['observed_date']}, {current_or_transition}, "
        f"64 active brands, 10 PAL additions, ZARA+SNIDEL configured, {len(inactive_brands)} legacy preserved, "
        f"7 external weekly signals, {len(proposals.get('proposals', []))} proposals, no sales estimation)"
    )


if __name__ == "__main__":
    main()
