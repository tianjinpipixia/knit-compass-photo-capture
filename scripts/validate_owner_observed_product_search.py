#!/usr/bin/env python3
"""Validate read-only owner-observed product candidates in the product-search UI."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "data/manual-intake/2026-08-18-american-holic-products-batch8.json"
INDEX = ROOT / "brand-intelligence/index.html"
AUGMENT = ROOT / "brand-intelligence/owner-observed-products.js"

batch = json.loads(BATCH.read_text(encoding="utf-8"))
items = batch.get("items", [])
assert len(items) == 2
assert all(item.get("review_status") == "PENDING" for item in items)
assert {item.get("payload", {}).get("productCode") for item in items} == {"0H001683100", "0H002151200"}
assert all(item.get("payload", {}).get("targetType") == "product" for item in items)

index = INDEX.read_text(encoding="utf-8")
assert "owner-observed-products.js" in index
assert "v=0.4.8" in index

script = AUGMENT.read_text(encoding="utf-8")
for required in (
    "2026-08-18-american-holic-products-batch8.json",
    "productSearch",
    "workflowFilter",
    "brandFilter",
    "workflowBoard",
    "STORE_CONFIRMED",
    "現物タグ確認",
    "Human Review前",
    "Human Reviewを開く",
    "PENDING",
    "kc-owner-observed-product",
):
    assert required in script, f"owner-observed product search missing: {required}"

# Read-only boundary: the augmentation may display PENDING candidates but must not
# write them into the master or browser state. Formal promotion remains Human Review only.
for forbidden in (
    "localStorage.setItem",
    "state.products.push",
    "review_status='APPROVED'",
    'review_status="APPROVED"',
):
    assert forbidden not in script, f"read-only candidate augmentation writes master state: {forbidden}"

print("owner-observed product search: OK (2 PENDING AMERICAN HOLIC candidates, read-only search display)")
