#!/usr/bin/env python3
"""Validate Knit Compass V04 install identity, Photo Capture surface, camera assets, and primary action order."""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail(f"invalid PNG: {path.name}")
    return struct.unpack(">II", data[16:24])


def main() -> None:
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    css = (ROOT / "app.css").read_text(encoding="utf-8")
    card_progress = (ROOT / "photo-capture-card-progress-v1.js").read_text(encoding="utf-8")
    icon = (ROOT / "icon.svg").read_text(encoding="utf-8")
    knitting = (ROOT / "knitting-ends-field.js").read_text(encoding="utf-8")
    service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")

    if manifest.get("name") != "Knit Compass V04":
        fail("installed full name must be Knit Compass V04")
    if manifest.get("short_name") != "Knit Compass":
        fail("installed short name must be Knit Compass")
    if manifest.get("id") != "./" or manifest.get("start_url") != "./brand-intelligence/" or manifest.get("scope") != "./":
        fail("stable V04 PWA id/start_url/scope is missing")
    expected = {"icon-192.png": (192, 192), "icon-512.png": (512, 512), "icon-maskable-512.png": (512, 512)}
    registered = {row.get("src"): row for row in manifest.get("icons", [])}
    for name, size in expected.items():
        if name not in registered or png_size(ROOT / name) != size:
            fail(f"missing or invalid installed icon: {name}")
    if "brand/knit-compass-mark.png" not in registered:
        fail("Knit Compass installed brand mark is missing")
    if png_size(ROOT / "icon-180.png") != (180, 180):
        fail("invalid Apple touch icon")
    if "camera icon" not in icon or "<circle" not in icon:
        fail("SVG camera icon is missing")
    for token in ('application-name" content="Knit Compass"', 'apple-mobile-web-app-title" content="Knit Compass"', '<title>Photo Capture | Knit Compass</title>', 'brand/knit-compass-mark.png'):
        if token not in index:
            fail(f"install metadata missing: {token}")
    primary = '<div class="primary-actions"><button id="new">新規キャプチャ</button><button class="secondary" id="exportHandoff">受信箱JSONを書き出す</button></div>'
    if primary not in app or app.find(primary) > app.find('<section class="card" id="inbox">'):
        fail("new capture/export actions are not above the inbox")
    if ".photo-grid{display:grid;gap:8px;margin-top:8px}" not in css:
        fail("photo upload spacing was not tightened")
    if "STYLEM" in index + app + json.dumps(manifest, ensure_ascii=False):
        fail("Photo Capture install surface contains legacy STYLEM naming")
    for token in ("写真・素材情報の登録", "下書き保存", "確認後に正式登録", "このMac専用", "外部へ自動送信しません"):
        if token not in app:
            fail(f"plain-language safety guidance missing: {token}")
    for stale in ("Independent Workspace", "独立Sandbox", "IndexedDB保存", "System ID:", "Revision:"):
        if stale in app + index:
            fail(f"Photo Capture sales surface exposes technical label: {stale}")
    if "const DISPLAY_VERSION = '1.3.3'" not in knitting or "current !== next" not in knitting:
        fail("non-recursive Photo Capture version disclosure guard is missing")
    if "knitting-ends-field.js?v=1.3.3" not in index:
        fail("Photo Capture helper cache-busting version is missing")
    if "serviceWorker.register('./sw.js?v=1.3.3-operational-hardening-4')" not in app:
        fail("Photo Capture install service worker is not registered")
    refresh = (ROOT / "sw-refresh-1.3.2.js").read_text(encoding="utf-8")
    for token in ("1.3.3-operational-hardening-4", "controllerchange", "location.reload()", "RELOAD_MARKER"):
        if token not in refresh:
            fail(f"Photo Capture stale-cache refresh is incomplete: {token}")
    if 'sw-refresh-1.3.2.js' not in index:
        fail("Photo Capture stale-cache refresh is not loaded")
    for stale in ("Independent Account ID", 'name="account" required pattern=', "IDまたはパスフレーズが違います", "${escapeHtml(session.displayName)} / ${escapeHtml(session.accountId)}", "内部ID"):
        if stale in app + (ROOT / "backup.js").read_text(encoding="utf-8"):
            fail(f"Photo Capture still exposes manual account ID entry: {stale}")
    for token in ("generatedAccountId", "accounts.length === 1", "パスフレーズだけ入力してください", "初回利用です。表示名とパスフレーズを設定してください。", "保存データを開く"):
        if token not in app:
            fail(f"Photo Capture simplified account flow is incomplete: {token}")
    if "indexedDB.open(DB_NAME, 1)" in app + (ROOT / "backup.js").read_text(encoding="utf-8"):
        fail("Photo Capture still rejects a newer compatible IndexedDB version")
    if "indexedDB.open(DB_NAME)" not in app or "indexedDB.open(DB_NAME)" not in (ROOT / "backup.js").read_text(encoding="utf-8"):
        fail("Photo Capture version-compatible IndexedDB open is missing")
    for token in ("missingStores", "db.version + 1", "REQUIRED_STORES"):
        if token not in app:
            fail(f"Photo Capture IndexedDB self-repair is missing: {token}")
    if "Account IDとパスフレーズ" in (ROOT / "backup.js").read_text(encoding="utf-8"):
        fail("backup restore still requires manual Account ID entry")
    backup = (ROOT / "backup.js").read_text(encoding="utf-8")
    for token in ("navigator.storage.persist", "kc_photo_capture_last_verified_backup_v1", "BACKUP_MAX_AGE_DAYS = 7", "バックアップを検証", "notifyDataChanged"):
        if token not in backup + app:
            fail(f"Photo Capture data protection is incomplete: {token}")
    if "if (!root || root.ownerDocument !== document || !root.isConnected) return;" not in card_progress or "ページ離脱中" not in card_progress:
        fail("Photo Capture async observer unload guard is missing")
    for token in ("kc-photo-capture-v1-3-3-operational-hardening-4", "./index.html", "./app.js", "./sw-refresh-1.3.2.js", "./icon-192.png", "./icon-512.png", "./brand/knit-compass-mark.png", "./brand-intelligence/", "./owner-yarns/", "./knit-image/", "./fabric-inspection/", "./market-intelligence/", "./data/yarn-catalog/mz100-catalog-3000.json", "./data/human-review/2026-08-15-intake-19-triage.json", "./data/brand-md-monitoring/latest-material-proposals.json", "./daily/", "./status/"):
        if token not in service_worker:
            fail(f"Photo Capture install service worker is incomplete: {token}")
    for destination in ("brand-intelligence/", "brand-intelligence/#cn-yarn-glossary", "owner-yarns/", "knit-image/", "fabric-inspection/", "market-intelligence/", "daily/", "customer-sharing/", "stylem/", "status/"):
        if f'href="{destination}"' not in index:
            fail(f"Photo Capture global navigation is missing: {destination}")

    print("OK: Knit Compass V04 install target, Photo Capture navigation, data protection, cache refresh, and safety boundaries")


if __name__ == "__main__":
    main()
