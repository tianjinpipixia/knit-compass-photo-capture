#!/usr/bin/env python3
"""Validate KIMI wave-2 China yarn glossary additions without weakening the base dictionary."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "brand-intelligence/data/cn-yarn-glossary.json"
WAVE2 = ROOT / "brand-intelligence/data/cn-yarn-glossary-wave2.json"
AUGMENT = ROOT / "brand-intelligence/siro-glossary-augment.js"

REQUIRED = {
    "螺旋纱／螺旋线",
    "波形纱／波形线",
    "辫子纱／小辫线",
    "结圈线",
    "蜈蚣纱",
    "彩点纱／点子纱",
    "段彩纱",
    "段染纱",
    "色纺纱／混色线",
    "金银丝／金银线",
    "珠片纱／亮片纱",
    "植绒纱／植绒线",
}
FANCY = {"螺旋纱／螺旋线", "波形纱／波形线", "辫子纱／小辫线", "结圈线", "蜈蚣纱"}
COLOR = {"彩点纱／点子纱", "段彩纱", "段染纱", "色纺纱／混色线"}
SPECIAL = {"金银丝／金银线", "珠片纱／亮片纱", "植绒纱／植绒线"}
HOLD_TERMS = {"牙刷纱", "乒乓纱", "菊花纱", "蝴蝶纱", "珠圈纱", "丝雨纱", "隆纹纱", "彩虹纱", "印花纱", "链条纱", "夹丝线", "毛巾纱", "梯子纱", "项链纱", "TT纱", "米粒纱", "云纹纱", "冰岛毛"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    base = load(BASE)
    wave = load(WAVE2)
    base_entries = base.get("entries", [])
    entries = wave.get("entries", [])
    require(wave.get("batch_id") == "KC-CN-YARN-WAVE2-20260819", "unexpected wave2 batch id")
    require(len(base_entries) >= 33, "base glossary unexpectedly shrank")
    require(len(entries) == 12, "wave2 must contain exactly 12 reviewed additions")

    base_names = {row.get("market_name") for row in base_entries}
    names = {row.get("market_name") for row in entries}
    require(names == REQUIRED, f"wave2 term set mismatch: {sorted(REQUIRED ^ names)}")
    require(not (base_names & names), "wave2 must not duplicate base market names")
    require(len(base_entries) + len(entries) >= 45, "combined glossary must expose at least 45 entries")

    ids = [row.get("id") for row in entries]
    priorities = [row.get("priority") for row in entries]
    require(len(ids) == len(set(ids)) and len(priorities) == len(set(priorities)), "wave2 ids/priorities must be unique")

    by_name = {row["market_name"]: row for row in entries}
    for term in FANCY:
        require(by_name[term]["category"] == "② ファンシー構造名", f"{term} category mismatch")
    for term in COLOR:
        require(by_name[term]["category"] == "⑤ 染色・色効果", f"{term} category mismatch")
    for term in SPECIAL:
        require(by_name[term]["category"] == "⑥ 特殊材料・複合", f"{term} category mismatch")

    require("FZ/T 12050-2015" in json.dumps(by_name["彩点纱／点子纱"], ensure_ascii=False), "彩点纱 standard evidence missing")
    require("段染" in by_name["段彩纱"]["natural_target_fiber"], "段彩纱 must be separated from 段染纱")
    require("成糸後" in by_name["段染纱"]["natural_target_fiber"], "段染纱 must remain a post-spinning color process")
    require("最終紡績方式" in by_name["色纺纱／混色线"]["natural_target_fiber"], "色纺 must not determine final spinning method")
    require("FZ/T 63026-2015" in json.dumps(by_name["金银丝／金银线"], ensure_ascii=False), "金银丝 standard evidence missing")
    require("静電" in json.dumps(by_name["植绒纱／植绒线"], ensure_ascii=False), "植绒 electrostatic-process evidence missing")

    serialized = json.dumps(entries, ensure_ascii=False)
    require(not any(term in serialized for term in HOLD_TERMS), "hold/C-rank terms must not be promoted into wave2")

    augment = AUGMENT.read_text(encoding="utf-8")
    for token in ("cn-yarn-glossary-wave2.json", "AB纱", "A，B纱", "并捻纺", "AB纱は独立構造へ増殖させずSiroの別名"):
        require(token in augment, f"Siro/wave2 augment missing token: {token}")

    print(f"PASS: KIMI wave2 adds {len(entries)} reviewed terms; combined glossary {len(base_entries)+len(entries)} entries; hold terms remain unpromoted")


if __name__ == "__main__":
    main()
