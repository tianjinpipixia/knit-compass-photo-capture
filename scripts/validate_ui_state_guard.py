#!/usr/bin/env python3
"""Regression checks for the Photo Capture 2.1.43 independent migration."""
from __future__ import annotations

import subprocess
from pathlib import Path

from tooling import require_node

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
CSS = ROOT / "app.css"
INDEX = ROOT / "index.html"
CAPTURE_INDEX = ROOT / "capture" / "index.html"
NODE = require_node()


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        fail(f"forbidden {label}: {needle}")


def main() -> None:
    app = APP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    index = INDEX.read_text(encoding="utf-8")
    capture_index = CAPTURE_INDEX.read_text(encoding="utf-8")

    result = subprocess.run([NODE, "--check", str(APP)], capture_output=True, text=True)
    if result.returncode:
        fail(f"JavaScript syntax error in app.js: {result.stderr.strip()}")

    for token in (
        'version: "2.1.43-independent.1"',
        'implementation_scope: "OWNER_DEVICE_DRAFT_WITH_PORTABLE_HANDOFF"',
        'authentication_realm: "KNIT_COMPASS_DEVICE_LOCAL"',
        'external_network_calls: "OFF"',
        'photo_store: "photos"',
        'event_store: "events"',
        'audit_store: "audit"',
    ):
        require(app, token, "independent 2.1.43 contract")

    for token in (
        "loadDeviceSession",
        "ensureImmediateDeviceSession",
        "renderDeviceAuth",
        "generatedAccountId",
        "passwordHash",
        "sessionStorage.setItem(SESSION_KEY",
        "if (accounts.length > 1) return null",
        'displayName: "Photo Capture利用者"',
        "if (!state.events.length) await openEditor()",
        "写真を撮る・素材を登録",
    ):
        require(app, token, "device-local authentication")
    forbid(app, "loadHostedSession", "Sites-only authentication dependency")

    for token in ("missingStores", "database.version + 1", "Object.values(STORES)"):
        require(app, token, "non-destructive IndexedDB self-repair")
    for token in (
        'dataState: "DRAFT"',
        'historyPolicy: "APPEND_ONLY"',
        'automaticSync: "OFF"',
        "state.isSaving",
        "STORES.audit",
        "snapshotSha256",
    ):
        require(app, token, "append-only DRAFT safety")

    form_start = app.find('<form id="kcCaptureForm"')
    form_end = app.find("</form>", form_start)
    if form_start < 0 or form_end < 0:
        fail("2.1.43 capture form is missing")
    form = app[form_start:form_end]
    ordered = ["登録日", "展示会 / 入手先", "糸商 / Supplier", "糸名・素材名", "資料区分", "2. 写真"]
    previous = -1
    for token in ordered:
        current = form.find(token, previous + 1)
        if current <= previous:
            fail(f"Photo Capture basic-item order is incorrect: {token}")
        previous = current
    for token in ("7分類", "全分類合計10枚", "本取り", "手配・進捗", "調査依頼"):
        require(form, token, "2.1.43 migrated field")

    require(css, ".kc-form-actions {", "form actions")
    require(css, "position: static;", "mobile non-overlapping actions")
    require(capture_index, 'body data-surface="mobile"', "mobile surface")

    for token in (
        "exportPortablePackage",
        "uploadPortableManifest",
        "sourceVersionMatch",
        "PHOTO_CAPTURE_2_1_${sourceVersionMatch[1]}_PORTABLE_ZIP",
        "2.1.41〜2.1.43 ZIPを取り込む",
        "DRAFT保存＋外部取込ZIP",
        "normalizeStandaloneSnapshot",
        "...existingSnapshot",
    ):
        require(app, token, "2.1.41–2.1.43 portable migration")

    for token in (
        "app.js?v=2.1.43-independent.1",
        "app.css?v=2.1.43-independent.1",
        "exhibition-supplier-master.js?v=2.1.43-independent.1",
        "knit-compass-ui.css?v=2.1.43-independent.1",
    ):
        require(index, token, "root independent cache key")
    for token in (
        "app.js?v=2.1.44-independent.10-immediate-entry",
        "app.css?v=2.1.44-independent.1",
        "exhibition-supplier-master.js?v=2.1.44-independent.1",
        "knit-compass-ui.css?v=2.1.44-independent.1",
        "sw-register.js?v=2.1.44-independent.10-immediate-entry",
    ):
        require(capture_index, token, "direct capture cache key")

    print("OK: Photo Capture 2.1.43 independent migration, DRAFT safety, data compatibility, and mobile action checks passed")


if __name__ == "__main__":
    main()
