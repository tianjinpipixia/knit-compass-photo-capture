#!/usr/bin/env python3
"""Guard merged work from being present in git but disconnected from Knit Compass V04."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    brand_index = (ROOT / "brand-intelligence/index.html").read_text(encoding="utf-8")
    owner_current = (ROOT / "owner-yarns/current.html").read_text(encoding="utf-8")
    intake = (ROOT / "owner-yarns/intake-current.html").read_text(encoding="utf-8")
    reflection = (ROOT / "brand-intelligence/v04-reflection-status.html").read_text(encoding="utf-8")

    # Retired Sites labels must never return as visible V04 navigation text.
    # Hidden compatibility metadata may remain until the older smoke checks are retired.
    assert ">展示会モード<" not in brand_index
    assert ">中国糸辞典<" not in brand_index
    assert ">中国糸名辞書<" not in brand_index

    # V04 navigation must expose the current surfaces, not a stale 24-item route.
    assert "中国糸名・素材名辞典" in brand_index
    assert "../owner-yarns/current.html" in brand_index
    assert "../owner-yarns/intake-current.html" in brand_index
    assert "25件（Winning Textile Levita含む）" in brand_index
    assert "./v04-reflection-status.html" in brand_index
    assert "../owner-yarns/\" target=\"_top\">糸検索" not in brand_index

    # V04 yarn-search wrapper prevents the old 24-item intake tab from becoming the current route.
    assert "./index.html" in owner_current
    assert "./intake-current.html" in owner_current
    assert "未反映25件・Human Review" in owner_current
    assert "Winning Textile Levita含む" in owner_current

    # Current intake must include every historical batch plus Winning Levita batch10.
    expected_batches = [
        "2026-08-08-weijie-hesheng-batch1.json",
        "2026-08-08-weihai-yaxin-chengyun-batch2.json",
        "2026-08-10-mz100-yarn-research-batch3.json",
        "2026-08-12-twin-win-company-factory-batch4.json",
        "2026-08-12-rope-picnic-gdm56050-batch5.json",
        "2026-08-13-american-holic-products-batch6.json",
        "2026-08-17-minghai-wool-silk-core-spun-batch7.json",
        "2026-08-18-american-holic-products-batch8.json",
        "2026-08-18-dinghong-mz100-25139-batch9.json",
        "2026-08-19-winning-textile-levita-batch10.json",
    ]
    assert "const EXPECTED_TOTAL=25" in intake
    assert "kc_v04_handoff_queue_v1" in intake
    for filename in expected_batches:
        assert filename in intake, f"current V04 intake missing {filename}"

    levita = load_json("data/manual-intake/2026-08-19-winning-textile-levita-batch10.json")
    levita_items = levita.get("items", [])
    assert len(levita_items) == 1
    assert levita_items[0].get("review_status") == "PENDING"
    payload = levita_items[0].get("payload", {})
    assert payload.get("yarnName") == "Levita / 利维纱"
    assert payload.get("countDisplay") == "1/40 Nm"
    assert payload.get("compositionRaw") == "78% Viscose / 22% Polyester"

    # #82 glossary remains reachable and retains the reviewed 33 + 13 = 46 dictionary composition.
    glossary = load_json("brand-intelligence/data/cn-yarn-glossary.json")
    wave2 = load_json("brand-intelligence/data/cn-yarn-glossary-wave2.json")
    base_entries = glossary.get("entries", [])
    wave2_entries = wave2.get("entries", [])
    assert len(base_entries) == 33
    assert len(wave2_entries) == 13
    assert len(base_entries) + len(wave2_entries) == 46
    assert "cn-yarn-glossary" in brand_index

    # #81 framework must stay at 11 Tier-A brands including SNIDEL and owner model roles.
    framework = load_json("config/brand-md-analysis-framework.json")
    tier_a = framework["scan_strategy"]["tier_a_deep_dive"]
    brands = tier_a.get("brands", {})
    assert tier_a.get("brand_count") == 11 == len(brands)
    assert brands.get("BR-00076") == "SNIDEL"
    fast = framework["cross_brand_relationships"]["fast_retailing_trend_to_life"]
    assert fast["trend_signal_brand"]["brand_name"] == "GU"
    assert fast["trend_signal_brand"]["role"] == "TREND"
    assert fast["life_translation_brand"]["brand_name"] == "UNIQLO"
    assert fast["life_translation_brand"]["role"] == "LIFE"

    # Latest pointer must not regress behind the 2026-08-20 corrected baseline,
    # and latest proposal pointer must match it.
    latest = load_json("data/brand-md-monitoring/latest.json")
    proposals = load_json("data/brand-md-monitoring/latest-material-proposals.json")
    observed = date.fromisoformat(latest["observed_date"])
    assert observed >= date(2026, 8, 20)
    assert proposals.get("observed_date") == latest.get("observed_date")
    assert latest.get("publication_status") == "PUBLISH_HOLD"
    assert proposals.get("publication_status") == "PUBLISH_HOLD"

    # Reflection status surface itself must load each source used above.
    for required in (
        "cn-yarn-glossary.json",
        "cn-yarn-glossary-wave2.json",
        "2026-08-19-winning-textile-levita-batch10.json",
        "brand-md-analysis-framework.json",
        "brand-md-monitoring/latest.json",
    ):
        assert required in reflection

    print(
        "V04 reflection guard: OK "
        "(retired visible Sites labels absent, current yarn-search route, glossary 33+13, 25-item intake incl. Levita, 11 Tier-A incl. SNIDEL, latest MD pointer aligned)"
    )


if __name__ == "__main__":
    main()
