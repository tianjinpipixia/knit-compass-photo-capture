#!/usr/bin/env python3
"""Build a lightweight, evidence-scoped MZ100 yarn search catalog.

The catalog stores only listing-page facts needed for discovery: source ID/URL,
listing name, count text, composition text and listed supplier. It never promotes
records to the confirmed yarn master. Detailed specifications still require
Human Review against the product page or supplier evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.mz100.cn/yarn"
TARGET_DEFAULT = 2000
OUTPUT_DEFAULT = Path("data/yarn-catalog/mz100-catalog-2000.json")
PRODUCT_PATH = re.compile(r"^/yarn/(\d+)$")
COUNT_PATTERN = re.compile(
    r"(?:\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\s*(?:NM|Nm|NE|Ne|S)|"
    r"\d+(?:\.\d+)?\s*(?:NM|Nm|NE|Ne|S|支|D|dtex|tex)|"
    r"\d+(?:\.\d+)?支)",
    re.IGNORECASE,
)
COMPANY_PATTERN = re.compile(r"(?:有限公司|有限责任公司|纺织厂|纺织品厂|毛织厂|公司)$")
FIBER_WORDS = (
    "棉", "毛", "羊绒", "羊驼", "腈纶", "晴纶", "涤纶", "聚酯", "锦纶", "尼龙",
    "粘胶", "粘纤", "黏胶", "莱赛尔", "天丝", "亚麻", "苎麻", "桑蚕丝", "真丝",
    "氨纶", "PBT", "PTT", "PPT", "铜氨", "醋酸", "再生", "植物纤维",
)


@dataclass(frozen=True)
class YarnListing:
    catalog_id: str
    source: str
    source_id: str
    source_url: str
    name: str
    count_display: str
    composition_raw: str
    listed_supplier: str
    catalog_status: str = "CATALOG_INDEXED"
    verification_status: str = "LISTING_PAGE_ONLY"
    master_status: str = "NOT_PROMOTED"


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def candidate_card(anchor: Tag, name: str) -> Tag:
    best: tuple[int, int, Tag] | None = None
    node: Tag | None = anchor
    for _ in range(9):
        parent = node.parent if isinstance(node, Tag) else None
        if not isinstance(parent, Tag):
            break
        node = parent
        product_links = {
            urlparse(link.get("href", "")).path
            for link in parent.find_all("a", href=True)
            if PRODUCT_PATH.fullmatch(urlparse(link.get("href", "")).path)
        }
        text = clean(parent.get_text("\n", strip=True))
        if not text or len(text) > 1000:
            continue
        if name not in text or len(product_links) > 1:
            continue
        lines = [clean(part) for part in parent.stripped_strings if clean(part)]
        score = 0
        if any(COUNT_PATTERN.search(line) for line in lines):
            score += 2
        if any("%" in line or "％" in line for line in lines):
            score += 2
        if any(COMPANY_PATTERN.search(line) for line in lines):
            score += 2
        score += min(2, sum(word in text for word in FIBER_WORDS))
        choice = (score, -len(text), parent)
        if best is None or choice[:2] > best[:2]:
            best = choice
    return best[2] if best else anchor


def parse_card(anchor: Tag, page_url: str) -> YarnListing | None:
    href = anchor.get("href", "")
    source_url = urljoin(page_url, href)
    match = PRODUCT_PATH.fullmatch(urlparse(source_url).path)
    name = clean(anchor.get_text(" ", strip=True))
    if not match or not name:
        return None

    card = candidate_card(anchor, name)
    lines = [clean(part) for part in card.stripped_strings if clean(part)]
    try:
        name_index = next(index for index, line in enumerate(lines) if line == name)
    except StopIteration:
        name_index = 0

    before = lines[max(0, name_index - 4):name_index]
    after = lines[name_index + 1:name_index + 8]
    count_display = ""
    for line in reversed(before):
        found = COUNT_PATTERN.search(line)
        if found:
            count_display = clean(found.group(0)).replace(" ", "")
            break
    if not count_display:
        for line in after[:2]:
            found = COUNT_PATTERN.search(line)
            if found:
                count_display = clean(found.group(0)).replace(" ", "")
                break

    listed_supplier = next((line for line in after if COMPANY_PATTERN.search(line)), "")
    composition_candidates = []
    for line in after:
        if line == listed_supplier or line == count_display or line == name:
            continue
        has_percent = "%" in line or "％" in line
        fiber_hits = sum(word in line for word in FIBER_WORDS)
        has_number = bool(re.search(r"\d", line))
        if has_percent or (has_number and fiber_hits >= 2):
            composition_candidates.append(line)
    composition_raw = composition_candidates[0] if composition_candidates else ""

    source_id = match.group(1)
    return YarnListing(
        catalog_id=f"CAT-MZ100-{source_id}",
        source="MZ100",
        source_id=source_id,
        source_url=source_url,
        name=name,
        count_display=count_display,
        composition_raw=composition_raw,
        listed_supplier=listed_supplier,
    )


def fetch_page(session: requests.Session, page: int, timeout: int) -> tuple[str, str]:
    response = session.get(BASE_URL, params={"page": page}, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding or "utf-8"
    return response.url, response.text


def build_catalog(target: int, delay: float, timeout: int, max_pages: int) -> list[YarnListing]:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; KnitCompassCatalogIndexer/1.0; evidence-only)",
        "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
    })
    records: dict[str, YarnListing] = {}
    empty_pages = 0

    for page in range(1, max_pages + 1):
        page_url, html = fetch_page(session, page, timeout)
        soup = BeautifulSoup(html, "html.parser")
        page_records = 0
        for anchor in soup.find_all("a", href=True):
            record = parse_card(anchor, page_url)
            if not record or record.source_id in records:
                continue
            records[record.source_id] = record
            page_records += 1
            if len(records) >= target:
                return list(records.values())[:target]
        empty_pages = empty_pages + 1 if page_records == 0 else 0
        if empty_pages >= 3:
            break
        if delay:
            time.sleep(delay)

    raise RuntimeError(f"Only {len(records)} unique yarn listings were collected; target={target}")


def write_catalog(records: list[YarnListing], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "catalog_id": "KC-YARN-CATALOG-MZ100-2000",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://www.mz100.cn/yarn",
        "record_count": len(records),
        "scope": "listing-page discovery index; Human Review required before master promotion",
        "records": [asdict(record) for record in records],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=TARGET_DEFAULT)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    if args.target < 1:
        raise SystemExit("target must be positive")
    catalog = build_catalog(args.target, args.delay, args.timeout, args.max_pages)
    write_catalog(catalog, args.output)
    print(f"wrote {len(catalog)} evidence-scoped yarn listings to {args.output}")


if __name__ == "__main__":
    main()
