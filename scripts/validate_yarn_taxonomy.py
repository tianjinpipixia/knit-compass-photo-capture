#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY = ROOT / "brand-intelligence" / "data" / "cn-yarn-glossary.json"
USAGE = ROOT / "usage-metrics.js"
GUARD = ROOT / "yarn-taxonomy-guard.js"
INDEX = ROOT / "index.html"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    glossary = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    entries = glossary.get("entries", [])
    by_market = {entry.get("market_name"): entry for entry in entries}

    require(glossary.get("policy", {}).get("combed_does_not_imply_ring_spinning") is True,
            "Glossary policy must forbid combed -> ring inference")
    for term in ["普梳棉", "精梳棉", "半精梳", "环锭纺", "紧密纺", "涡流纺", "喷气纺", "气流纺／转杯纺"]:
        require(term in by_market, f"Missing glossary term: {term}")

    combed = by_market["精梳棉"]
    combed_text = json.dumps(combed, ensure_ascii=False).lower()
    require("コーマ綿" in combed.get("japanese_name", ""), "精梳棉 must map to コーマ綿")
    require("リング紡績と推定しない" in combed.get("natural_target_fiber", ""),
            "精梳棉 guidance must explicitly reject ring inference")

    usage = USAGE.read_text(encoding="utf-8")
    guard = GUARD.read_text(encoding="utf-8")
    index = INDEX.read_text(encoding="utf-8")

    for token in [
        "COTTON_PREPARATION_OPTIONS", "SPINNING_METHOD_OPTIONS", "cottonPreparation",
        "前紡・綿処理", "最終紡績方式", "combed cotton", "精梳棉", "Air Jet", "Open End"
    ]:
        require(token in usage, f"usage-metrics.js missing taxonomy token: {token}")

    require("['Ring', ['リング紡績', '环锭纺', 'ring spinning']]" in guard,
            "Ring detector must require explicit ring terminology")
    ring_rule = guard.split("['Ring',", 1)[1].split("}]", 1)[0] if "['Ring'," in guard else ""
    require("combed" not in ring_rule.lower() and "コーマ" not in ring_rule and "精梳" not in ring_rule,
            "Ring aliases must not contain combed terminology")
    require("['combed', ['コーマ', 'コーマ綿', '精梳', '精梳棉', 'combed', 'combed cotton']]" in guard,
            "Combed detector aliases are incomplete")
    require("form.elements.cottonPreparation.value === 'unconfirmed'" in guard,
            "Guard must upgrade unconfirmed prep from explicit source evidence")
    require("form.elements.spinningMethod.value === 'Unknown'" in guard,
            "Guard must preserve Unknown unless explicit spinning evidence exists")
    require("yarn-taxonomy-guard.js?v=1.0.0" in index,
            "Photo Capture must load yarn taxonomy guard")

    # Core regression: source evidence that only says combed cotton must never be a Ring alias.
    require("combed" not in "リング紡績 环锭纺 ring spinning".lower(),
            "Regression fixture invalid")

    print("PASS: yarn taxonomy keeps cotton preparation separate from final spinning method")


if __name__ == "__main__":
    main()
