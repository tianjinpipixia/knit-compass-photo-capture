#!/usr/bin/env python3
"""Validate the nine evidence-backed official product-link completions."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/brand-research/2026-08-09-product-link-completion-batch3.csv"
WORK = ROOT / "data/brand-research/2026-08-08-product78-next-work.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


rows = read(DATA)
assert len(rows) == 9
assert len({row["product_id"] for row in rows}) == 9
assert Counter(row["brand_name"] for row in rows) == {"GLOBAL WORK": 3, "GU": 3, "MUJI": 3}
assert Counter(row["current_scope"] for row in rows) == {"WOMEN_KNIT": 8, "OUT_OF_SCOPE_MENS_UNISEX": 1}
assert all(row["verification_result"] == "OFFICIAL_CURRENT_EXACT_MATCH" for row in rows)
assert all(row["checked_date"] == "2026-08-09" for row in rows)

expected = {
    "TMP_NBR_BRNC_0005_0002": ("650269", "www.dot-st.com"),
    "TMP_NBR_BRNC_0005_0003": ("655851", "www.dot-st.com"),
    "TMP_NBR_BRNC_0005_0001": ("902751", "www.dot-st.com"),
    "TMP_NBR_BRNC_0016_0003": ("361744", "www.gu-global.com"),
    "TMP_NBR_BRNC_0016_0002": ("360752", "www.gu-global.com"),
    "TMP_NBR_BRNC_0016_0001": ("361701", "www.gu-global.com"),
    "TMP_NBR_BRNC_0019_0002": ("23157735", "www.muji.com"),
    "TMP_NBR_BRNC_0019_0001": ("23158312", "www.muji.com"),
    "TMP_NBR_BRNC_0019_0003": ("23000789", "www.muji.com"),
}

for row in rows:
    code, domain = expected[row["product_id"]]
    parsed = urlparse(row["official_url"])
    assert row["official_code"] == code
    assert parsed.scheme == "https"
    assert parsed.netloc == domain
    assert row["official_url"] not in {"", "NOT AVAILABLE"}
    if domain != "www.muji.com":
        assert code in parsed.path

excluded = next(row for row in rows if row["product_id"] == "TMP_NBR_BRNC_0016_0003")
assert excluded["current_scope"] == "OUT_OF_SCOPE_MENS_UNISEX"

work = {row["work_bucket"]: row for row in read(WORK)}
assert "NO_URL_TARGET_PENDING" not in work
assert work["NO_URL_TARGET_OFFICIAL_MATCHED"]["count"] == "9"
assert work["NO_URL_TARGET_OFFICIAL_MATCHED"]["status"] == "DONE_WITH_ONE_SCOPE_EXCLUSION"
assert sum(int(row["count"]) for key, row in work.items() if key != "TOTAL") == 78

print("product link completion: OK (9/9 official URLs; 8 women + 1 evidence-backed scope exclusion)")
