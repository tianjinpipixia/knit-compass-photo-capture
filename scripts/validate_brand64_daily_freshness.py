#!/usr/bin/env python3
"""Validate the latest 64-brand daily observation and optional freshness."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "data/brand-md-monitoring/latest.json"
PROPOSALS = ROOT / "data/brand-md-monitoring/latest-material-proposals.json"


def repository_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    path.relative_to(ROOT.resolve())
    return path


def valid_http_url(value: str) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-age-days", type=int)
    args = parser.parse_args()

    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    proposals = json.loads(PROPOSALS.read_text(encoding="utf-8"))
    observed_date = date.fromisoformat(latest["observed_date"])

    assert latest.get("format") == "KC_BRAND64_MD_LATEST_POINTER"
    assert latest.get("sales_quantity_policy") == "NO_ESTIMATION"
    assert latest.get("publication_status") == "PUBLISH_HOLD"
    assert proposals.get("format") == "KC_BRAND64_MATERIAL_PROPOSALS"
    assert proposals.get("observed_date") == latest.get("observed_date")
    assert proposals.get("observed_brand_count") == 64
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

    rows = [json.loads(line) for line in daily_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 64
    brand_ids = [row.get("id") or row.get("brand_id") for row in rows]
    assert len(set(brand_ids)) == 64
    assert all((row.get("d") or row.get("observed_date")) == latest["observed_date"] for row in rows)
    assert all(valid_http_url(row.get("u") or row.get("source")) for row in rows)
    assert all((row.get("q") or row.get("sales_quantity_status")) in {"NA", "NOT_AVAILABLE"} for row in rows)
    assert all((row.get("p") or row.get("publication_status")) in {"HOLD", "PUBLISH_HOLD"} for row in rows)

    if args.max_age_days is not None:
        age_days = (date.today() - observed_date).days
        assert age_days <= args.max_age_days, (
            f"brand64 daily observation is stale: observed={observed_date}, age_days={age_days}, "
            f"allowed={args.max_age_days}"
        )

    print(
        f"brand64 daily freshness: OK ({latest['observed_date']}, 64 brands, "
        f"{len(proposals.get('proposals', []))} material proposals, no sales estimation)"
    )


if __name__ == "__main__":
    main()
