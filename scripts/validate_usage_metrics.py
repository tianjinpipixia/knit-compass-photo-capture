#!/usr/bin/env python3
"""Validate privacy-preserving local usage metrics and KPI export wiring."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "usage-metrics.js").read_text(encoding="utf-8")
SW = (ROOT / "sw.js").read_text(encoding="utf-8")
STATUS = (ROOT / "status/index.html").read_text(encoding="utf-8")

for token in (
    "kc_usage_metrics_v1",
    "DAILY_AGGREGATES_NO_INPUT_CONTENT",
    "MAX_DAYS = 120",
    "measurement_date",
    "active_user_count",
    "入力内容・氏名・検索語を保存しない日次集計",
    "KnitCompassMetrics",
):
    assert token in SCRIPT, f"usage metrics missing: {token}"

assert "event.target.value" not in SCRIPT
assert "FormData" not in SCRIPT
assert "./usage-metrics.js" in SW
assert "kcUsageSummary" in STATUS
assert "kcExportUsageMetrics" in STATUS

surfaces = (
    "index.html",
    "brand-intelligence/app.html",
    "owner-yarns/index.html",
    "market-intelligence/index.html",
    "knit-image/index.html",
    "fabric-inspection/index.html",
    "daily/index.html",
    "customer-sharing/index.html",
    "stylem/index.html",
    "status/index.html",
)
for relative in surfaces:
    assert "usage-metrics.js" in (ROOT / relative).read_text(encoding="utf-8"), f"metrics not loaded: {relative}"

print("usage metrics: OK (daily counts only, no names/search terms/input contents, KPI CSV export wired)")
