#!/usr/bin/env python3
"""Validate fabric inspection and market intelligence safety boundaries."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f"{label} missing: {token}")


def forbid(text: str, token: str, label: str) -> None:
    if token in text:
        raise AssertionError(f"{label} must not contain: {token}")


def check_javascript(path: Path) -> None:
    node = shutil.which("node")
    if node:
        result = subprocess.run([node, "--check", str(path)], check=False, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


fabric_html = (ROOT / "fabric-inspection/index.html").read_text(encoding="utf-8")
fabric_js = (ROOT / "fabric-inspection/app.js").read_text(encoding="utf-8")
market_html = (ROOT / "market-intelligence/index.html").read_text(encoding="utf-8")
market_js = (ROOT / "market-intelligence/app.js").read_text(encoding="utf-8")

for html, label in ((fabric_html, "fabric inspection"), (market_html, "market intelligence")):
    for destination in ("../brand-intelligence/", "../", "../owner-yarns/", "../daily/", "../status/"):
        require(html, f'href="{destination}"', label)
    require(html, "PENDING_HUMAN_REVIEW", label)
    require(html, "自動", label)

for javascript, label, storage_key, export_format in (
    (fabric_js, "fabric inspection", "kc_fabric_inspection_records_v1", "KC_FABRIC_INSPECTION_EXPORT"),
    (market_js, "market intelligence", "kc_market_intelligence_observations_v1", "KC_MARKET_INTELLIGENCE_EXPORT"),
):
    require(javascript, storage_key, label)
    require(javascript, export_format, label)
    require(javascript, "review_status:'PENDING_HUMAN_REVIEW'", label)
    require(javascript, "publication_status:'HOLD'", label)
    require(javascript, ".push(", label)
    forbid(javascript, "kc_independent_practical_v0_4", label)
    forbid(javascript, "kc_v04_handoff_queue_v1", label)
    forbid(javascript, "XMLHttpRequest", label)
    forbid(javascript, "WebSocket", label)

for token in ("fetch(", "fetch('http", 'fetch("http'):
    forbid(fabric_js, token, "fabric inspection")

for token in (
    "COTTON", "WOOL", "LINEN", "NYLON", "POLYESTER", "RECYCLED_POLYESTER",
    "country_code:'CN'", "market_scope:'CHINA'", "SOURCE_AS_WRITTEN_NO_CONVERSION",
    "validUrl", "SOURCE_CHECKED", "SUPPLIER_CONFIRMED", "latest-material-proposals.json",
    "NOT_PROMOTED", "owner-yarns/?query=", "knit-image/?source=catalog",
):
    require(market_js, token, "market intelligence")
for token in (
    "中国ベース 6原料比較", "綿", "ウール", "麻", "ナイロン", "ポリエステル",
    "再生ポリエステル", "64ブランド日次MD", "推定値で穴埋めしません", "SALES NOT AVAILABLE", "No automatic conversion",
):
    require(market_html, token, "market intelligence")
for token in ("fetch('http", 'fetch("http', "XMLHttpRequest", "WebSocket"):
    forbid(market_js, token, "market intelligence")

check_javascript(ROOT / "fabric-inspection/app.js")
check_javascript(ROOT / "market-intelligence/app.js")

print("operational surfaces: OK (append-only local records, Human Review and publication boundaries preserved)")
