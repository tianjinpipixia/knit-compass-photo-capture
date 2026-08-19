#!/usr/bin/env python3
"""Validate the China yarn market-name glossary and sales navigation contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "brand-intelligence/data/cn-yarn-glossary.json"
PAGE = ROOT / "brand-intelligence/yarn-glossary.html"
SHELL = ROOT / "brand-intelligence/index.html"
PRESERVED = ROOT / "brand-intelligence/index-current.html"
SW = ROOT / "brand-intelligence/sw.js"

REQUIRED_MARKET_NAMES = {
    "仿貂毛／仿貂绒",
    "仿兔毛／仿兔绒",
    "仿羊绒",
    "仿马海毛",
    "仿狐狸毛",
    "仿羊驼",
    "仿亚麻",
    "冰麻／丝麻",
}
REQUIRED_FANCY_TERMS = {
    "花捻纱／花式捻线",
    "双曲纱",
    "圈圈纱／圈圈线",
    "结子纱／结子线",
    "大肚纱／粗节纱",
    "竹节纱",
    "羽毛纱",
    "睫毛纱",
    "带子纱／扁带纱",
    "空心带／筒状纱",
    "雪尼尔纱",
    "拉毛纱",
    "磨毛纱／刷毛纱",
    "小马海／仿马海",
    "皮毛纱／仿皮草纱",
    "色纺拉毛纱",
}
REQUIRED_FIELDS = {
    "id",
    "priority",
    "market_name",
    "aliases",
    "japanese_name",
    "representative_yarn_types",
    "common_fibers",
    "category",
    "natural_target_fiber",
    "search_keywords",
    "exhibition_checks",
}
REQUIRED_MAIN_NAV = {
    "商品調査": "./index-current.html",
    "Photo Capture": "../",
    "中国糸名辞書": "./yarn-glossary.html",
    "糸検索": "../owner-yarns/",
    "編み地イメージ": "../knit-image/",
    "生地検査": "../fabric-inspection/",
    "原料相場": "../market-intelligence/",
    "Daily": "../daily/",
    "共有管理": "../customer-sharing/",
    "顧客ポータル": "../stylem/",
    "システム状態": "../status/",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def main() -> None:
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read glossary JSON: {error}")

    if data.get("schema_version") != "1.1.0":
        fail("unexpected glossary schema_version")
    if data.get("dictionary_id") != "KC-CN-YARN-001":
        fail("dictionary_id must be KC-CN-YARN-001")

    policy = data.get("policy") or {}
    if policy.get("market_name_is_not_composition") is not True:
        fail("market names must not be treated as composition")
    if policy.get("natural_fiber_must_be_verified_from_composition") is not True:
        fail("natural fiber verification policy is missing")
    if policy.get("combed_does_not_imply_ring_spinning") is not True:
        fail("combed cotton must not imply ring spinning")
    if policy.get("fancy_market_terms_do_not_determine_structure") is not True:
        fail("fancy market terms must not determine yarn structure")
    if policy.get("post_process_does_not_determine_base_structure") is not True:
        fail("post process terms must not determine base yarn structure")
    if policy.get("representative_field_label") != "代表的な糸タイプ（例）":
        fail("representative field label must be 代表的な糸タイプ（例）")
    if policy.get("avoid_field_label") != "糸例":
        fail("avoid_field_label must preserve the rejected label 糸例")

    entries = data.get("entries")
    if not isinstance(entries, list) or len(entries) < 32:
        fail("at least 32 glossary entries are required after fancy-yarn expansion")

    ids: set[str] = set()
    priorities: set[int] = set()
    names: set[str] = set()
    by_name: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            fail("every glossary entry must be an object")
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            fail(f"{entry.get('id', '?')} missing fields: {sorted(missing)}")
        entry_id = str(entry["id"])
        if entry_id in ids:
            fail(f"duplicate id: {entry_id}")
        ids.add(entry_id)
        priority = entry["priority"]
        if not isinstance(priority, int) or priority < 1 or priority in priorities:
            fail(f"invalid or duplicate priority: {priority}")
        priorities.add(priority)
        name = str(entry["market_name"]).strip()
        if not name:
            fail(f"{entry_id} has empty market_name")
        names.add(name)
        by_name[name] = entry
        for field in ("aliases", "representative_yarn_types", "common_fibers", "search_keywords", "exhibition_checks"):
            value = entry[field]
            if not isinstance(value, list) or not value or not all(str(item).strip() for item in value):
                fail(f"{entry_id} {field} must be a non-empty string array")
        if not str(entry["japanese_name"]).strip() or not str(entry["category"]).strip():
            fail(f"{entry_id} Japanese name/category must be present")
        if not str(entry["natural_target_fiber"]).strip():
            fail(f"{entry_id} natural fiber caution is required")

    missing_names = REQUIRED_MARKET_NAMES - names
    if missing_names:
        fail(f"missing initial market names: {sorted(missing_names)}")
    missing_fancy = REQUIRED_FANCY_TERMS - names
    if missing_fancy:
        fail(f"missing fancy yarn terms: {sorted(missing_fancy)}")

    structure_terms = {
        "花捻纱／花式捻线", "双曲纱", "圈圈纱／圈圈线", "结子纱／结子线",
        "大肚纱／粗节纱", "竹节纱", "羽毛纱", "睫毛纱", "带子纱／扁带纱",
        "空心带／筒状纱", "雪尼尔纱",
    }
    for term in structure_terms:
        if by_name[term]["category"] != "① ファンシー構造名":
            fail(f"{term} must be categorized as ① ファンシー構造名")
    for term in ("拉毛纱", "磨毛纱／刷毛纱"):
        if by_name[term]["category"] != "③ 後加工名":
            fail(f"{term} must be categorized as ③ 後加工名")
    for term in ("小马海／仿马海", "皮毛纱／仿皮草纱"):
        if by_name[term]["category"] != "④ 市場呼称・外観名":
            fail(f"{term} must be categorized as ④ 市場呼称・外観名")
    if by_name["色纺拉毛纱"]["category"] != "④ 複合市場呼称":
        fail("色纺拉毛纱 must be categorized as ④ 複合市場呼称")
    if "元の糸構造を自動的に決めない" not in by_name["拉毛纱"]["natural_target_fiber"]:
        fail("拉毛纱 must not imply a base yarn structure")
    if "花捻や特定紡績方式を確定しない" not in by_name["色纺拉毛纱"]["natural_target_fiber"]:
        fail("色纺拉毛纱 must not imply 花捻 or a spinning method")

    page = PAGE.read_text(encoding="utf-8")
    for token in (
        "中国語糸名 ↔ 日本語標準名",
        "代表的な糸タイプ（例）",
        "kc_independent_practical_v0_4",
        "cn-yarn-glossary.json",
        "正式糸マスター",
        "天然対象繊維",
    ):
        if token not in page:
            fail(f"glossary page missing token: {token}")
    if "糸例</" in page:
        fail("glossary UI must not use the rejected label 糸例")

    shell = SHELL.read_text(encoding="utf-8")
    if "中国糸名辞書" not in shell or "./index-current.html" not in shell or "./yarn-glossary.html" not in shell:
        fail("sales shell is not wired to the preserved Human Review UI and glossary")
    for label, route in REQUIRED_MAIN_NAV.items():
        if label not in shell:
            fail(f"sales navigation missing label: {label}")
        if route not in shell:
            fail(f"sales navigation missing route for {label}: {route}")
    leading_labels = ("商品調査", "糸検索", "原料相場", "編み地イメージ", "生地検査", "Photo Capture", "中国糸名辞書", "Daily", "管理")
    if any(shell.find(left) > shell.find(right) for left, right in zip(leading_labels, leading_labels[1:])):
        fail("sales navigation leading order is incorrect")

    if shell.count('class="nav-item') != 9:
        fail("sales top navigation must contain exactly 9 primary controls")
    for token in ("管理メニュー", "manageButton", "manageMenu", 'aria-expanded="false"'):
        if token not in shell:
            fail(f"sales management menu missing token: {token}")
    management_menu = shell[shell.find('id="manageMenu"'):]
    for label in ("Human Review", "共有管理", "顧客ポータル", "システム状態"):
        if f"<strong>{label}</strong>" not in management_menu:
            fail(f"{label} must be grouped inside the management menu")

    if not PRESERVED.exists():
        fail("preserved Human Review shell is missing")

    sw = SW.read_text(encoding="utf-8")
    for path in ("./index-current.html", "./yarn-glossary.html", "./data/cn-yarn-glossary.json"):
        if path not in sw:
            fail(f"service worker cache missing {path}")

    print(f"OK: validated {len(entries)} China yarn entries including fancy-yarn taxonomy and sales navigation")


if __name__ == "__main__":
    main()
