#!/usr/bin/env python3
"""Regression checks for Photo Capture → Human Review safety."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from tooling import require_node

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.js"
INBOX = ROOT / "brand-intelligence" / "index-current.html"
NODE = require_node()


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def node_check(path: Path) -> None:
    result = subprocess.run([NODE, "--check", str(path)], capture_output=True, text=True)
    if result.returncode:
        fail(f"JavaScript syntax error in {path}: {result.stderr.strip()}")


def extract_inline_script(html: str) -> str:
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)
    if not scripts:
        fail("brand-intelligence/index-current.html has no inline Human Review script")
    return scripts[-1]


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def forbid(text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text):
        fail(f"forbidden {label}: {pattern}")


def simulate_compaction() -> None:
    queue = [
        *({"id": f"P-{index}", "status": "PENDING"} for index in range(520)),
        *({"id": f"A-{index}", "status": "APPROVED"} for index in range(100)),
    ]
    pending = [item for item in queue if item["status"] == "PENDING"]
    reviewed = [item for item in queue if item["status"] != "PENDING"]
    compacted = [*pending, *reviewed[: max(0, 500 - len(pending))]]
    if len([item for item in compacted if item["status"] == "PENDING"]) != 520:
        fail("queue compaction simulation dropped pending candidates")


def simulate_composition_percentages() -> None:
    program = r"""
const total = text => [...String(text || '').matchAll(/(\d+(?:\.\d+)?)\s*[%％]/g)]
  .map(match => Number(match[1]))
  .reduce((sum, value) => sum + value, 0);
const cases = [
  ['TENCEL A100 80% NY 20%', 100],
  ['粘胶80％ 尼龙20％', 100],
  ['G100 80％ NY 20%', 100],
];
for (const [text, expected] of cases) {
  if (total(text) !== expected) throw new Error(`${text}: ${total(text)} !== ${expected}`);
}
"""
    result = subprocess.run([NODE, "-e", program], capture_output=True, text=True)
    if result.returncode:
        fail(f"composition percentage simulation failed: {result.stderr.strip()}")


def main() -> None:
    app_text = APP.read_text(encoding="utf-8")
    inbox_html = INBOX.read_text(encoding="utf-8")
    inline_script = extract_inline_script(inbox_html)

    node_check(APP)
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(inline_script)
        inline_path = Path(handle.name)
    try:
        node_check(inline_path)
    finally:
        inline_path.unlink(missing_ok=True)

    forbid(app_text, r"queue\.slice\(0,\s*500\)", "blind Photo Capture queue truncation")
    forbid(inline_script, r"queue\.slice\(0,\s*500\)", "blind Human Review queue truncation")
    require(app_text, "compactHandoffQueue", "Photo Capture queue compaction")
    require(app_text, "saveHandoffQueue", "Photo Capture queue save guard")
    require(app_text, "item.review_status === 'PENDING'", "Photo Capture pending retention")
    require(inline_script, "compactQueue", "Human Review queue compaction")
    require(inline_script, "item.review_status==='PENDING'", "Human Review pending retention")
    require(inline_script, "hasMeaningfulValue", "partial upsert protection")
    require(inline_script, "preferIncoming", "existing master preservation")
    require(inline_script, "payload.targetType==='organization'?payload.targetId:''", "organization target ID mapping")
    require(inline_script, "state.photoCaptureIdMap[payload.targetId]=ids.organizationId", "stable organization ID mapping")
    require(inline_script, "if(hasMeaningfulValue(value))existing[key]=value", "non-empty-only upsert")
    require(app_text, "handoffForEvent", "event-version-specific handoff status")
    require(app_text, "saveInProgress", "Photo Capture duplicate-save guard")
    require(app_text, "matchAll(/(\\d+(?:\\.\\d+)?)\\s*[%％]/g)", "half/full-width percentage composition total")
    require(app_text, "let handoffError = null", "DRAFT-preserving handoff failure handling")
    require(app_text, "下書きは保存しましたが、Human Review受信箱へ送信できませんでした", "handoff retry guidance")
    require(inline_script, "normalizeStatus", "normalized weak status protection")
    require(inline_script, "'未確認','候補','推定'", "Japanese weak statuses")
    require(inline_script, "saveApproval", "atomic approval storage")
    require(inline_script, "restoreStorage", "approval rollback")
    require(inline_script, "busyHandoffs", "duplicate approval guard")
    require(inline_script, "return{ids,state}", "deferred master save")
    require(inline_script, "isEvidenceBacked", "evidence-backed yarn field filter")
    require(inline_script, "evidenceValue(payload.countValue,payload)", "count evidence gate")
    require(inline_script, "compositionConfirmed?payload.compositionRaw:''", "composition evidence gate")
    require(inline_script, "organizationProfile:profile", "organization profile persistence")
    require(inline_script, "resolveOrganizationProfiles", "organization relationship ID resolution")
    require(inline_script, "relatedOrganizationId", "formal related organization ID persistence")
    require(inline_script, "state.photoCaptureIdMap[payload.sourceOrganizationId]=ids.organizationId", "source organization temporary ID mapping")
    forbid(inline_script, r"saveState\(state\);return ids", "one-sided approval save")

    simulate_compaction()
    simulate_composition_percentages()
    print("OK: Human Review safety checks passed")


if __name__ == "__main__":
    main()
