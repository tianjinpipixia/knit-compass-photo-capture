#!/usr/bin/env python3
"""Keep sales-facing labels current while preserving internal compatibility IDs."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = (
    "app.js",
    "app-state-guard.js",
    "index.html",
    "brand-intelligence/index.html",
    "brand-intelligence/index-current.html",
    "brand-intelligence/app.html",
    "brand-intelligence/yarn-glossary.html",
    "brand-intelligence/manifest.webmanifest",
    "customer-sharing/index.html",
    "daily/index.html",
    "fabric-inspection/index.html",
    "knit-image/index.html",
    "knit-image/app.js",
    "owner-yarns/index.html",
    "status/index.html",
)
STALE_LABELS = (
    "V04 TOP",
    "V04本体",
    "V04・Human Review",
    "v0.4受信箱",
    "糸検索2,000件",
    "糸マスター2,000件",
    "V04糸マスター",
    "端末内V04",
    "独立実用版 v0.4",
    "Photo Capture受信箱",
    "KC-V04-INBOX",
    "サーバー同期パイロット",
    "この端末のv0.4データ",
)

for relative in SURFACES:
    text = (ROOT / relative).read_text(encoding="utf-8")
    for label in STALE_LABELS:
        assert label not in text, f"{relative} exposes stale sales label: {label}"

photo_capture = (ROOT / "app.js").read_text(encoding="utf-8")
human_review = (ROOT / "brand-intelligence/index-current.html").read_text(encoding="utf-8")
assert "KC_V04_INBOX_ITEM" in photo_capture, "internal handoff format must remain compatible"
assert "kc_v04_handoff_queue_v1" in photo_capture, "internal queue key must remain compatible"
assert "kc_independent_practical_v0_4" in human_review, "internal master key must remain compatible"
assert "Human Review受信箱" in photo_capture, "Photo Capture must use the current inbox label"

print("sales labels: OK (current terminology shown; internal V04 compatibility IDs preserved)")
