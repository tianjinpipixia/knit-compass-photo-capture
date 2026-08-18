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
EXPECTED_PAL_IDS = {f"BR-{i:05d}" for i in range(65, 75)}
EXPECTED_INACTIVE_IDS = {
    "BR-00026", "BR-00029", "BR-00034", "BR-00037", "BR-00038",
    "BR-00043", "BR-00044", "BR-00045", "BR-00046", "BR-00061",
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


def row_id(row: dict) -> str:
    return str(row.get("id") or row.get("brand_id") or "")


def row_name(row: dict) -> str:
    return str(row.get("b") or row.get("brand") or row.get("brand_name") or "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-age-days", type=int)
    args = parser.parse_args()

    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    proposals = json.loads(PROPOSALS.read_text(encoding="utf-8"))
    active_config = json.loads(ACTIVE_CONFIG.read_text(encoding="utf-8"))
    observed_date = date.fromisoformat(latest["observed_date"])

    assert active_config.get("format") == "KC_BRAND64_ACTIVE_SET"
    active_brands = active_config.get("active_brands", {})
    inactive_brands = active_config.get("inactive_legacy_brands", {})
    assert active_config.get("active_brand_count") == 64 == len(active_brands)
    assert active_config.get("inactive_legacy_count") == 10 == len(inactive_brands)
    assert len(set(active_brands.values())) == 64
    assert len(set(inactive_brands.values())) == 10
    assert not (set(active_brands) & set(inactive_brands))
    assert set(inactive_brands) == EXPECTED_INACTIVE_IDS
    assert EXPECTED_PAL_IDS <= set(active_brands)
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

    primary_rows = load_jsonl(daily_path)
    overlay_paths = [repository_path(p) for p in latest.get("active_daily_overlay_paths", [])]
    overlay_rows = []
    for path in overlay_paths:
        assert path.is_file()
        overlay_rows.extend(load_jsonl(path))
    assert latest.get("active_daily_overlay_paths") == proposals.get("active_daily_overlay_paths")

    all_rows = primary_rows + overlay_rows
    active_rows = [row for row in all_rows if row_id(row) in active_brands]
    active_ids = [row_id(row) for row in active_rows]
    assert len(active_rows) == 64
    assert len(set(active_ids)) == 64
    assert set(active_ids) == set(active_brands)
    for row in active_rows:
        brand_id = row_id(row)
        assert row_name(row) == active_brands[brand_id]
        assert (row.get("d") or row.get("observed_date")) == latest["observed_date"]
        assert valid_http_url(row.get("u") or row.get("source"))
        assert (row.get("q") or row.get("sales_quantity_status")) in {"NA", "NOT_AVAILABLE"}
        assert (row.get("p") or row.get("publication_status")) in {"HOLD", "PUBLISH_HOLD"}

    # Old 10 remain in historical primary data but are excluded from the active 64.
    legacy_present = {row_id(row) for row in primary_rows if row_id(row) in inactive_brands}
    assert legacy_present == EXPECTED_INACTIVE_IDS
    assert not (EXPECTED_INACTIVE_IDS & set(active_ids))

    pal_active_rows = [row for row in active_rows if row_id(row) in EXPECTED_PAL_IDS]
    assert len(pal_active_rows) == 10
    assert all("palcloset.jp" in (row.get("u") or "") for row in pal_active_rows)

    if args.max_age_days is not None:
        age_days = (date.today() - observed_date).days
        assert age_days <= args.max_age_days, (
            f"brand64 daily observation is stale: observed={observed_date}, age_days={age_days}, "
            f"allowed={args.max_age_days}"
        )

    print(
        f"brand64 active daily freshness: OK ({latest['observed_date']}, 64 active brands, "
        f"10 PAL additions, 10 legacy preserved, {len(proposals.get('proposals', []))} proposals, "
        "no sales estimation)"
    )


if __name__ == "__main__":
    main()
