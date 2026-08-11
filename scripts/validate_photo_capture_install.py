#!/usr/bin/env python3
"""Validate Photo Capture PWA naming, camera icon assets, and primary action order."""
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
    icon = (ROOT / "icon.svg").read_text(encoding="utf-8")
    knitting = (ROOT / "knitting-ends-field.js").read_text(encoding="utf-8")
    service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")

    if manifest.get("name") != "Photo Capture":
        fail("installed full name must be Photo Capture")
    if manifest.get("short_name") != "Photo Capture":
        fail("installed short name must be Photo Capture")
    if manifest.get("id") != "./" or manifest.get("start_url") != "./":
        fail("stable PWA id/start_url is missing")
    expected = {"icon-192.png": (192, 192), "icon-512.png": (512, 512), "icon-maskable-512.png": (512, 512)}
    registered = {row.get("src"): row for row in manifest.get("icons", [])}
    for name, size in expected.items():
        if name not in registered or png_size(ROOT / name) != size:
            fail(f"missing or invalid installed icon: {name}")
    if png_size(ROOT / "icon-180.png") != (180, 180):
        fail("invalid Apple touch icon")
    if "camera icon" not in icon or "<circle" not in icon:
        fail("SVG camera icon is missing")
    for token in ('application-name" content="Photo Capture"', 'apple-mobile-web-app-title" content="Photo Capture"', '<title>Photo Capture</title>', 'icon-180.png'):
        if token not in index:
            fail(f"install metadata missing: {token}")
    primary = '<div class="primary-actions"><button id="new">新規キャプチャ</button><button class="secondary" id="exportHandoff">受信箱JSONを書き出す</button></div>'
    if primary not in app or app.find(primary) > app.find('<section class="card" id="inbox">'):
        fail("new capture/export actions are not above the inbox")
    if ".photo-grid{display:grid;gap:8px;margin-top:8px}" not in css:
        fail("photo upload spacing was not tightened")
    if "STYLEM" in index + app + json.dumps(manifest, ensure_ascii=False):
        fail("Photo Capture install surface contains legacy STYLEM naming")
    for token in ("ONLY YOU", "DRAFT FIRST", "INBOX UPLOAD", "AUTO MASTER OFF", "PUBLISH HOLD"):
        if token not in app:
            fail(f"safety badge missing: {token}")
    if "const DISPLAY_VERSION = '1.3.1'" not in knitting or "current !== next" not in knitting:
        fail("non-recursive Photo Capture version disclosure guard is missing")
    if "knitting-ends-field.js?v=1.3.1" not in index:
        fail("Photo Capture helper cache-busting version is missing")
    if "serviceWorker.register('./sw.js?v=1.3.1')" not in app:
        fail("Photo Capture install service worker is not registered")
    for token in ("kc-photo-capture-v1-3-1", "./index.html", "./app.js", "./icon-192.png", "./icon-512.png"):
        if token not in service_worker:
            fail(f"Photo Capture install service worker is incomplete: {token}")
    for destination in ("brand-intelligence/", "owner-yarns/", "daily/", "customer-sharing/", "status/"):
        if f'href="{destination}"' not in index:
            fail(f"Photo Capture global navigation is missing: {destination}")

    print("OK: Photo Capture install naming, camera icons, service worker, global navigation, action order, and safety badges")


if __name__ == "__main__":
    main()
