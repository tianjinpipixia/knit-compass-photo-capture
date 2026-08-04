#!/usr/bin/env python3
"""Apply the final full-width percentage and registry documentation corrections."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"ERROR: missing {label}")


def blob(path: str) -> str:
    result = subprocess.run(
        ["git", "hash-object", f"--path={path}", "--", path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    app = read("app.js")
    app = replace_once(app, "const APP_VERSION = '1.2.2';", "const APP_VERSION = '1.2.3';", "app version")
    app = replace_once(
        app,
        r"matchAll(/(\d+(?:\.\d+)?)\s*%/g)",
        r"matchAll(/(\d+(?:\.\d+)?)\s*[%％]/g)",
        "composition percentage parser",
    )
    write("app.js", app)
    app_sha = blob("app.js")

    index = read("index.html")
    index = index.replace("manifest.webmanifest?v=1.2.2", "manifest.webmanifest?v=1.2.3")
    index = index.replace("版: v1.2.2", "版: v1.2.3")
    index = index.replace("app.js?v=1.2.2", "app.js?v=1.2.3")
    index = re.sub(r"Revision: [0-9a-f]{12}", f"Revision: {app_sha[:12]}", index, count=1)
    write("index.html", index)
    index_sha = blob("index.html")

    validator = read("scripts/validate_handoff_safety.py")
    validator = replace_once(
        validator,
        r'require(app_text, r"matchAll(/(\d+(?:\.\d+)?)\s*%/g)", "percentage-only composition total")',
        r'require(app_text, r"matchAll(/(\d+(?:\.\d+)?)\s*[%％]/g)", "half/full-width percentage composition total")',
        "composition validator",
    )
    write("scripts/validate_handoff_safety.py", validator)

    guard_sha = blob("app-state-guard.js")
    brand_index_sha = blob("brand-intelligence/index.html")
    brand_sw_sha = blob("brand-intelligence/sw.js")

    registry_path = ROOT / "config/system-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["schema_version"] = "1.2.3"
    registry["updated_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    for system in registry["systems"]:
        if system["system_id"] == "KC-PHOTO-CAPTURE":
            system["display_version"] = "v1.2.3"
            system["code_revision"] = f"git-blob:{app_sha}"
            for source in system.get("auxiliary_sources", []):
                if source.get("code_source") == "app-state-guard.js@main":
                    source["code_revision"] = f"git-blob:{guard_sha}"
                elif source.get("code_source") == "index.html@main":
                    source["code_revision"] = f"git-blob:{index_sha}"
        elif system["system_id"] == "KC-V04-WEB":
            for source in system.get("auxiliary_sources", []):
                if source.get("code_source") == "brand-intelligence/index.html@main":
                    source["code_revision"] = f"git-blob:{brand_index_sha}"
                elif source.get("code_source") == "brand-intelligence/sw.js@main":
                    source["code_revision"] = f"git-blob:{brand_sw_sha}"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = read("README.md").replace("Photo Capture v1.2.2", "Photo Capture v1.2.3")
    readme = readme.replace(
        "TENCEL A100等の品名数字を混率へ誤加算しません。",
        "TENCEL A100等の品名数字を混率へ誤加算せず、半角%・全角％の両方を認識します。",
    )
    write("README.md", readme)

    handoff = read("docs/PHOTO_CAPTURE_HANDOFF.md").replace("版: 1.0.2", "版: 1.0.3")
    handoff = handoff.replace(
        "混率合計は`%`付き数値だけを対象とし、`TENCEL A100`や`G100`の数字は加算しません。",
        "混率合計は半角`%`または全角`％`付き数値だけを対象とし、`TENCEL A100`や`G100`の数字は加算しません。",
    )
    write("docs/PHOTO_CAPTURE_HANDOFF.md", handoff)

    system_doc = read("docs/SYSTEM_REGISTRY.md")
    system_doc = system_doc.replace("版: 1.2.2", "版: 1.2.3")
    photo_row = (
        f"| `KC-PHOTO-CAPTURE` | Photo Capture | 独立Sandbox | `v1.2.3` | "
        f"`app.js@main` / `git-blob:{app_sha[:12]}…`。補助: `app-state-guard.js` / `{guard_sha[:8]}…`、"
        f"`app.css` / `3fa9acda…`、`index.html` / `{index_sha[:8]}…`、`backup.js` / `5f7dee4a…` | "
        "IndexedDB `kc_independent_photo_capture_v1_0`、sessionStorage `kc_session_v1`・`kc_photo_capture_editor_draft_v1`、受信箱localStorage `kc_v04_handoff_queue_v1` | "
        "同一ブラウザ受信箱＋手動JSON / PENDINGを全件保持し確認済み履歴から整理 | なし | 稼働中 |"
    )
    v04_row = (
        f"| `KC-V04-WEB` | Knit Compass 独立実用版 v0.4 | 独立運用 | `v0.4.5` | "
        f"本体 `brand-intelligence/app.html` / `52f174f3…`。Human Review入口 `brand-intelligence/index.html` / `{brand_index_sha[:8]}…`。SW `{brand_sw_sha[:8]}…` | "
        "localStorage `kc_independent_practical_v0_4`、受信箱 `kc_v04_handoff_queue_v1` | "
        "候補受信、JSON取込、既存値保護・失敗時復元付きHuman Review反映 | Production / Core / Company DBへの自動接続なし | 稼働中 |"
    )
    system_doc, photo_count = re.subn(r"^\| `KC-PHOTO-CAPTURE` .*?$", photo_row, system_doc, count=1, flags=re.MULTILINE)
    system_doc, v04_count = re.subn(r"^\| `KC-V04-WEB` .*?$", v04_row, system_doc, count=1, flags=re.MULTILINE)
    if photo_count != 1 or v04_count != 1:
        raise SystemExit("ERROR: system registry documentation rows not found")
    write("docs/SYSTEM_REGISTRY.md", system_doc)

    print("OK: full-width composition and registry documentation corrections applied")


if __name__ == "__main__":
    main()
