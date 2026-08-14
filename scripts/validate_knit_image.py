#!/usr/bin/env python3
"""Validate the read-only yarn-to-knit image surface and its direct entry routes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "knit-image/index.html").read_text(encoding="utf-8")
JS = (ROOT / "knit-image/app.js").read_text(encoding="utf-8")
OWNER = (ROOT / "owner-yarns/index.html").read_text(encoding="utf-8")
V04 = (ROOT / "brand-intelligence/app.html").read_text(encoding="utf-8")

for token in (
    'id="yarnQuery"', 'id="gauge"', 'id="knitStructure"',
    'id="knittingEnds"', 'id="knitCanvas"', 'id="downloadPng"',
    "検討用イメージ", "外部AI送信なし", "マスター書込なし",
):
    assert token in HTML, f"knit image HTML missing {token}"

for token in (
    "kc_independent_practical_v0_4",
    "../data/yarn-catalog/mz100-catalog-3000.json",
    "../data/yarn-catalog/mz100-catalog-2000.json",
    "localStorage.getItem(V04_KEY)",
    "knittingEnds",
    "STRUCTURE_LABELS",
    "drawFabric",
    ".toBlob(",
    "端末内で生成しました",
):
    assert token in JS, f"knit image JavaScript missing {token}"

assert "localStorage.setItem" not in JS, "generator must not write browser master storage"
assert "indexedDB" not in JS, "generator must not write Photo Capture storage"
assert "fetch('http" not in JS and 'fetch("http' not in JS, "generator must not transmit to an external API"

assert "../knit-image/?source=catalog&amp;id=${encodeURIComponent(row.catalog_id)}" in OWNER
assert "../knit-image/?source=master&id=${encodeURIComponent(y.id)}" in V04
print("knit image: OK (read-only inputs, separate gauge/structure/ends, local Canvas PNG, direct routes)")
