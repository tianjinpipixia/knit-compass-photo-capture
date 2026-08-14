#!/usr/bin/env python3
"""Rebuild the deterministic two-part compatibility payload from app.html."""
from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "brand-intelligence" / "app.html"
TARGETS = (
    ROOT / "brand-intelligence" / "payload-01.b64",
    ROOT / "brand-intelligence" / "payload-02.b64",
)

raw = SOURCE.read_bytes()
encoded = base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")
split_at = (len(encoded) + 1) // 2
chunks = (encoded[:split_at], encoded[split_at:])
for target, chunk in zip(TARGETS, chunks):
    target.write_text(chunk + "\n", encoding="ascii")

print(f"rebuilt payload: {len(raw)} bytes, SHA-256 {hashlib.sha256(raw).hexdigest()}")
