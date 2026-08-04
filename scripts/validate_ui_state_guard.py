#!/usr/bin/env python3
"""Regression checks for Photo Capture save, resend, and editor recovery guards."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
GUARD = ROOT / "app-state-guard.js"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def main() -> None:
    if not GUARD.exists():
        fail("app-state-guard.js is missing")

    index_text = INDEX.read_text(encoding="utf-8")
    guard_text = GUARD.read_text(encoding="utf-8")

    result = subprocess.run(["node", "--check", str(GUARD)], capture_output=True, text=True)
    if result.returncode:
        fail(f"JavaScript syntax error: {result.stderr.strip()}")

    require(index_text, 'app-state-guard.js?v=1.0.0', "guard script include")
    if index_text.index("app-state-guard.js") < index_text.index("app.js?v=1.2.1"):
        fail("guard must load after app.js")

    require(guard_text, "const dedupeKey = `${recordId}:${version}`", "version-specific handoff state")
    require(guard_text, "button.disabled = sent", "completed send button lock")
    require(guard_text, "form.checkValidity()", "send validation guard")
    require(guard_text, "setFormBusy(form, true)", "save double-submit guard")
    require(guard_text, "EDITOR_DRAFT_KEY", "editor draft recovery")
    require(guard_text, "sessionStorage.removeItem(EDITOR_DRAFT_KEY)", "draft cleanup after save")

    print("OK: Photo Capture UI state guard checks passed")


if __name__ == "__main__":
    main()
