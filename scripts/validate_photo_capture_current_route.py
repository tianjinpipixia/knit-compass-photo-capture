#!/usr/bin/env python3
"""Validate the legacy /photo-capture-current/ compatibility route."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / "photo-capture-current" / "index.html"
SW = ROOT / "sw.js"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        fail(f"missing {label}: {token}")


def main() -> None:
    if not COMPAT.is_file():
        fail("photo-capture-current/index.html is missing")

    html = COMPAT.read_text(encoding="utf-8")
    service_worker = SW.read_text(encoding="utf-8")

    require(html, 'data-compat-route="photo-capture-current"', "compatibility route marker")
    require(html, 'http-equiv="refresh" content="0; url=../"', "no-JavaScript redirect")
    require(html, '<link rel="canonical" href="../">', "canonical current Photo Capture target")
    require(html, '<a href="../">Photo Captureを開く</a>', "manual fallback link")
    require(html, "const target = new URL('../', location.href);", "current Photo Capture target resolver")
    require(html, "const legacyScopePath = new URL('./', location.href).pathname;", "legacy service-worker scope resolver")
    require(html, "registration.unregister()", "legacy nested service-worker cleanup")
    require(html, "location.replace(target.href)", "history-replacing redirect")

    # Keep this compatibility route out of the root app shell so the network copy can
    # supersede an obsolete deployed build instead of being pinned by the root cache.
    if "./photo-capture-current/" in service_worker or "./photo-capture-current/index.html" in service_worker:
        fail("photo-capture-current must remain network-first and outside the root app shell")

    print("OK: /photo-capture-current/ redirects to the current Photo Capture and clears only its legacy nested service worker")


if __name__ == "__main__":
    main()
