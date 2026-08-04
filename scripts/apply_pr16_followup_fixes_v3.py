#!/usr/bin/env python3
"""Run the PR #16 follow-up patch with tolerant HTML escaping matching."""
from __future__ import annotations

import re

import apply_pr16_followup_fixes as patch


original_replace_once = patch.replace_once


def tolerant_replace_once(text: str, old: str, new: str, label: str) -> str:
    if label == "HTML quote escaping":
        updated, count = re.subn(r"&quot(?=')", "&quot;", text, count=1)
        if count == 1:
            return updated
        if "&quot;'" in text:
            return text
        patch.fail("could not find HTML quote escaping")
    return original_replace_once(text, old, new, label)


patch.replace_once = tolerant_replace_once
patch.main()
