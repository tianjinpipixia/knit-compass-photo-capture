#!/usr/bin/env python3
"""Validate the 2,000-record yarn catalog and remaining-work intake surface."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/yarn-catalog/mz100-catalog-2000.json"
PAGE = ROOT / "owner-yarns/index.html"
BATCHES = [
    ROOT / "data/manual-intake/2026-08-08-weijie-hesheng-batch1.json",
    ROOT / "data/manual-intake/2026-08-08-weihai-yaxin-chengyun-batch2.json",
    ROOT / "data/manual-intake/2026-08-10-mz100-yarn-research-batch3.json",
    ROOT / "data/manual-intake/2026-08-12-twin-win-company-factory-batch4.json",
    ROOT / "data/manual-intake/2026-08-12-rope-picnic-gdm56050-batch5.json",
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
assert sum(bool(str(row.get("name") or "").strip()) for row in records) == 2000
assert sum(bool(str(row.get("listed_supplier") or "").strip()) for row in records) >= 1500
assert sum(bool(str(row.get("composition_raw") or "").strip()) for row in records) >= 1500

all_items = []
for path in BATCHES:
    assert path.is_file(), f"missing batch: {path.name}"
    batch = json.loads(path.read_text(encoding="utf-8"))
    assert batch.get("format") == "KC_V04_INBOX_EXPORT"
    assert isinstance(batch.get("items"), list) and batch["items"]
    assert all(item.get("review_status") == "PENDING" for item in batch["items"])
    all_items.extend(batch["items"])

assert len(all_items) == 17
assert len({item.get("dedupe_key") for item in all_items}) == 17
assert any(item.get("payload", {}).get("sourceOrganizationName", "").startswith("TWIN WIN") for item in all_items)
gdm = [item for item in all_items if item.get("payload", {}).get("productCode") == "GDM56050"]
assert len(gdm) == 1
assert gdm[0]["payload"]["productName"] == ""
assert gdm[0]["payload"]["compositionRaw"] == ""
assert gdm[0]["payload"]["verificationStatus"] == "candidate"

html = PAGE.read_text(encoding="utf-8")
for required in (
    "mz100-catalog-2000.json",
    "kc_v04_handoff_queue_v1",
    "17件",
    "GDM56050",
    "TWIN WIN",
    "Human Review",
    "会社スプレッドシート用CSV",
):
    assert required in html, f"owner-yarns page missing: {required}"

print("owner yarn implementation: OK (2000 catalog records, 17 PENDING candidates, safety boundary preserved)")
