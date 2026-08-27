#!/usr/bin/env python3
"""Validate the independent Photo Capture 2.1.43 install and safety contract."""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_BUILD = "2.1.43-independent.1"
CAPTURE_BUILD = "2.1.44-independent.10-immediate-entry"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        fail(f"missing {label}: {token}")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail(f"invalid PNG: {path.name}")
    return struct.unpack(">II", data[16:24])


def main() -> None:
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    capture_manifest = json.loads((ROOT / "capture" / "manifest.webmanifest").read_text(encoding="utf-8"))
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    capture_index = (ROOT / "capture" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    css = (ROOT / "app.css").read_text(encoding="utf-8")
    backup = (ROOT / "backup.js").read_text(encoding="utf-8")
    worker = (ROOT / "sw.js").read_text(encoding="utf-8")
    capture_worker = (ROOT / "capture" / "sw.js").read_text(encoding="utf-8")
    capture_register = (ROOT / "capture" / "sw-register.js").read_text(encoding="utf-8")
    refresh = (ROOT / "sw-refresh-1.3.2.js").read_text(encoding="utf-8")
    supplier_master = (ROOT / "exhibition-supplier-master.js").read_text(encoding="utf-8")

    if manifest.get("name") != "Knit Compass V04" or manifest.get("short_name") != "Knit Compass":
        fail("stable Knit Compass PWA identity changed")
    if manifest.get("id") != "./" or manifest.get("start_url") != "./brand-intelligence/" or manifest.get("scope") != "./":
        fail("stable V04 PWA id/start_url/scope is missing")
    if capture_manifest.get("start_url") != f"./?build={CAPTURE_BUILD}" or capture_manifest.get("scope") != "./":
        fail("independent Photo Capture PWA start URL is stale")

    expected = {"icon-192.png": (192, 192), "icon-512.png": (512, 512), "icon-maskable-512.png": (512, 512)}
    for name, size in expected.items():
        if png_size(ROOT / name) != size:
            fail(f"missing or invalid installed icon: {name}")

    for token in (
        f"app.js?v={CONTRACT_BUILD}",
        f"app.css?v={CONTRACT_BUILD}",
        f"exhibition-supplier-master.js?v={CONTRACT_BUILD}",
        f"knit-compass-ui.css?v={CONTRACT_BUILD}",
    ):
        require(index, token, "root independent Photo Capture asset")
    for token in (
        f"app.js?v={CAPTURE_BUILD}",
        "app.css?v=2.1.44-independent.1",
        "exhibition-supplier-master.js?v=2.1.44-independent.1",
        "knit-compass-ui.css?v=2.1.44-independent.1",
        f"sw-register.js?v={CAPTURE_BUILD}",
    ):
        require(capture_index, token, "direct Photo Capture asset")
    require(capture_index, 'body data-surface="mobile"', "mobile capture surface")

    for token in (
        'version: "2.1.43-independent.1"',
        'implementation_scope: "OWNER_DEVICE_DRAFT_WITH_PORTABLE_HANDOFF"',
        'authentication_realm: "KNIT_COMPASS_DEVICE_LOCAL"',
        'external_network_calls: "OFF"',
        'automatic_sync: "OFF_PORTABLE_ZIP_ONLY"',
        "renderDeviceAuth",
        "ensureImmediateDeviceSession",
        "passwordHash",
        "generatedAccountId",
        "missingStores",
        "database.version + 1",
    ):
        require(app, token, "independent runtime contract")
    if "loadHostedSession" in app:
        fail("independent Photo Capture still requires Sites authentication")
    for token in ("KC_COMPANY_WORK_API", "photo-capture-owner-finalize", "uploadRecordToInbox"):
        if token in app:
            fail(f"independent Photo Capture still contains a direct API upload path: {token}")
    for document in (index, capture_index, worker, capture_worker):
        for token in ("knitting-ends-field.js", "photo-capture-card-progress-v1.js", "app-state-guard.js"):
            if token in document:
                fail(f"active Photo Capture shell still loads a compatibility-only asset: {token}")

    for token in (
        'dataState: "DRAFT"',
        'historyPolicy: "APPEND_ONLY"',
        'automaticSync: "OFF"',
        "snapshotSha256",
        "STORES.audit",
        "state.isSaving",
        "normalizeStandaloneSnapshot",
        "...existingSnapshot",
    ):
        require(app, token, "DRAFT/data compatibility safety")

    form_start = app.find('<form id="kcCaptureForm"')
    form_end = app.find("</form>", form_start)
    if form_start < 0 or form_end < 0:
        fail("2.1.43 capture form is missing")
    editor = app[form_start:form_end]
    previous = -1
    for token in ("登録日", "展示会 / 入手先", "糸商 / Supplier", "糸名・素材名", "資料区分", "2. 写真"):
        current = editor.find(token, previous + 1)
        if current <= previous:
            fail(f"Photo Capture basic-item order is incorrect: {token}")
        previous = current
    for token in ("7分類", "全分類合計10枚", "本取り", "手配・進捗", "調査依頼", "端末にDRAFT保存", "DRAFT保存＋外部取込ZIP"):
        require(editor, token, "2.1.43 migrated surface")
    require(css, ".kc-form-actions {", "form action layout")
    require(css, "position: static;", "mobile action non-overlap")

    for token in (
        "exportPortablePackage",
        "uploadPortableManifest",
        "sourceVersionMatch",
        "PHOTO_CAPTURE_2_1_${sourceVersionMatch[1]}_PORTABLE_ZIP",
        "2.1.41〜2.1.43 ZIPを取り込む",
        "原本は変更せず",
    ):
        require(app, token, "portable 2.1.41–2.1.43 migration")
    require(supplier_master, "KC_EXHIBITION_SUPPLIER_MASTER_V1", "exhibition Supplier candidates")

    for token in (
        "navigator.storage.persist",
        "kc_photo_capture_last_verified_backup_v1",
        "BACKUP_MAX_AGE_DAYS = 7",
        "バックアップを検証",
        "notifyDataChanged",
        "kcInbox",
        "main.kc-app",
    ):
        require(backup + app, token, "data protection")

    for token in (
        "kc-photo-capture-v2-1-43-independent-1",
        "./app.js",
        "./app.css",
        "./knit-compass-ui.css",
        "./exhibition-supplier-master.js",
        "./sw-refresh-1.3.2.js",
        "./brand-intelligence/",
        "./owner-yarns/",
        "./knit-image/",
        "./fabric-inspection/",
        "./market-intelligence/",
        "./daily/",
        "./status/",
    ):
        require(worker, token, "root service-worker shell")
    require(capture_worker, "kc-photo-capture-independent-v14-v2144-immediate-entry", "capture service-worker cache")
    require(capture_worker, "../exhibition-supplier-master.js", "capture Supplier master cache")
    require(capture_worker, "../knit-compass-ui.css", "capture UI cache")
    require(capture_register, f"./sw.js?v=${{SW_VERSION}}", "capture service-worker registration")
    require(capture_register, CAPTURE_BUILD, "capture service-worker version")
    for token in (CONTRACT_BUILD, "controllerchange", "location.reload()", "RELOAD_MARKER"):
        require(refresh, token, "stale-cache refresh")

    for destination in (
        "brand-intelligence/",
        "brand-intelligence/#cn-yarn-glossary",
        "owner-yarns/",
        "knit-image/",
        "fabric-inspection/",
        "market-intelligence/",
        "daily/",
        "customer-sharing/",
        "stylem/",
        "status/",
    ):
        require(index, f'href="{destination}"', "global navigation")

    print("OK: Photo Capture 2.1.43 independent install, migration, cache, and safety boundaries")


if __name__ == "__main__":
    main()
