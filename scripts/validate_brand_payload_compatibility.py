#!/usr/bin/env python3
"""Keep the direct product-research HTML, compressed payload, and CI pins aligned."""
from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "brand-intelligence"
APP = BRAND / "app.html"
PAYLOADS = (BRAND / "payload-01.b64", BRAND / "payload-02.b64")
WORKFLOWS = (
    ROOT / ".github/workflows/validate-independent-v0-4.yml",
    ROOT / ".github/workflows/build-android-daily-apk.yml",
)

direct = APP.read_bytes()
encoded = "".join(path.read_text(encoding="ascii").strip() for path in PAYLOADS)
reconstructed = gzip.decompress(base64.b64decode(encoded, validate=True))
digest = hashlib.sha256(direct).hexdigest()

assert reconstructed == direct, "compressed compatibility payload does not match app.html"
for workflow in WORKFLOWS:
    text = workflow.read_text(encoding="utf-8")
    assert digest in text, f"{workflow.name} does not pin the current app.html SHA-256"

print(f"brand payload compatibility: OK ({len(direct)} bytes, SHA-256 {digest})")
