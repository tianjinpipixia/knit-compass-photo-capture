#!/usr/bin/env python3
"""Apply final safety fixes and make the existing UI guard validator version-safe."""
from __future__ import annotations

import apply_final_save_review_safety as patch


original_patch_versions = patch.patch_versions_workflow_and_tests


def patch_versions_and_version_safe_tests() -> None:
    original_patch_versions()

    path = "scripts/validate_ui_state_guard.py"
    text = patch.read(path)
    text = patch.replace_once(
        text,
        "import subprocess\nfrom pathlib import Path",
        "import re\nimport subprocess\nfrom pathlib import Path",
        "UI validator regex import",
    )
    text = patch.replace_once(
        text,
        "    if index_text.index(\"app-state-guard.js\") < index_text.index(\"app.js?v=1.2.1\"):\n        fail(\"guard must load after app.js\")",
        "    app_script = re.search(r'app\\.js\\?v=[^\"\\']+', index_text)\n    if not app_script:\n        fail(\"app.js script include is missing\")\n    if index_text.index(\"app-state-guard.js\") < app_script.start():\n        fail(\"guard must load after app.js\")",
        "version-safe UI script order check",
    )
    patch.write(path, text)

    handoff_path = "scripts/validate_handoff_safety.py"
    handoff = patch.read(handoff_path)
    handoff = handoff.replace(
        'require(app_text, "matchAll(/(\\d+(?:\\.\\d+)?)\\s*%/g)", "percentage-only composition total")',
        'require(app_text, r"matchAll(/(\\d+(?:\\.\\d+)?)\\s*%/g)", "percentage-only composition total")',
    )
    patch.write(handoff_path, handoff)


patch.patch_versions_workflow_and_tests = patch_versions_and_version_safe_tests
patch.main()
