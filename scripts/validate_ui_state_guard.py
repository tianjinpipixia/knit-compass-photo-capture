#!/usr/bin/env python3
"""Regression checks for Photo Capture save, resend, editor recovery, and knitting ends."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from tooling import require_node

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
GUARD = ROOT / "app-state-guard.js"
KNITTING_ENDS = ROOT / "knitting-ends-field.js"
NODE = require_node()


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def node_check(path: Path) -> None:
    result = subprocess.run([NODE, "--check", str(path)], capture_output=True, text=True)
    if result.returncode:
        fail(f"JavaScript syntax error in {path.name}: {result.stderr.strip()}")


def main() -> None:
    for path in (GUARD, KNITTING_ENDS):
        if not path.exists():
            fail(f"{path.name} is missing")

    index_text = INDEX.read_text(encoding="utf-8")
    guard_text = GUARD.read_text(encoding="utf-8")
    knitting_text = KNITTING_ENDS.read_text(encoding="utf-8")

    node_check(GUARD)
    node_check(KNITTING_ENDS)

    require(index_text, 'app-state-guard.js?v=1.0.0', "guard script include")
    require(index_text, 'knitting-ends-field.js?v=1.3.2', "knitting ends script include")
    app_script = re.search(r'app\.js\?v=[^"\']+', index_text)
    if not app_script:
        fail("app.js script include is missing")
    knitting_position = index_text.index("knitting-ends-field.js")
    guard_position = index_text.index("app-state-guard.js")
    if knitting_position < app_script.start():
        fail("knitting ends field must load after app.js")
    if guard_position < knitting_position:
        fail("UI state guard must load after knitting ends field")

    require(guard_text, "const dedupeKey = `${recordId}:${version}`", "version-specific handoff state")
    require(guard_text, "button.disabled = sent", "completed send button lock")
    require(guard_text, "form.checkValidity()", "send validation guard")
    require(guard_text, "setFormBusy(form, true)", "save double-submit guard")
    require(guard_text, "EDITOR_DRAFT_KEY", "editor draft recovery")
    require(guard_text, "sessionStorage.removeItem(EDITOR_DRAFT_KEY)", "draft cleanup after save")

    require(knitting_text, "const FIELD_NAME = 'knittingEnds'", "knitting ends data key")
    require(knitting_text, "value.snapshot[FIELD_NAME] = ends", "IndexedDB event enrichment")
    require(knitting_text, "value.snapshot.dataContractVersion = DATA_CONTRACT_VERSION", "data contract version update")
    require(knitting_text, "stripEndsFromGauge", "combined gauge migration")
    require(knitting_text, "kc_photo_capture_knitting_ends_v1", "UI restore sidecar")
    require(knitting_text, "本取り（編地）", "visible knitting ends label")

    print("OK: Photo Capture UI state guard and knitting ends checks passed")


if __name__ == "__main__":
    main()
