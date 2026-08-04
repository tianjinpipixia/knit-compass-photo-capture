#!/usr/bin/env python3
"""Run the PR #16 follow-up patch with a tolerant HTML-escape pre-fix."""
from __future__ import annotations

import apply_pr16_followup_fixes as patch


original_patch_v04 = patch.patch_v04


def patch_v04_tolerant() -> None:
    path = "brand-intelligence/index.html"
    text = patch.read(path)
    if "'&quot'" in text and "'&quot;'" not in text:
        patch.write(path, text.replace("'&quot'", "'&quot;'", 1))
    original_patch_v04()


patch.patch_v04 = patch_v04_tolerant
patch.main()
