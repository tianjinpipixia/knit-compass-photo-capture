#!/usr/bin/env python3
"""Validate the master → approved customer snapshot → request return boundary."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "customer-sharing" / "policy.js"
ADMIN = ROOT / "customer-sharing" / "index.html"
PORTAL = ROOT / "stylem" / "index.html"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        fail(f"forbidden {label}: {needle}")


def node_check_text(text: str, label: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(text)
        path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            fail(f"JavaScript syntax error in {label}: {result.stderr.strip()}")
    finally:
        path.unlink(missing_ok=True)


def inline_scripts(html: str) -> list[str]:
    return re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)


def function_block(text: str, name: str) -> str:
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{(.*?)\n\s*\}}", text, flags=re.DOTALL)
    if not match:
        fail(f"missing function block: {name}")
    return match.group(1)


def main() -> None:
    for path in (POLICY, ADMIN, PORTAL):
        if not path.exists():
            fail(f"missing file: {path.relative_to(ROOT)}")

    policy = POLICY.read_text(encoding="utf-8")
    admin = ADMIN.read_text(encoding="utf-8")
    portal = PORTAL.read_text(encoding="utf-8")

    node_check_text(policy, "customer-sharing/policy.js")
    for index, script in enumerate(inline_scripts(admin), start=1):
        node_check_text(script, f"customer-sharing/index.html inline script {index}")
    for index, script in enumerate(inline_scripts(portal), start=1):
        node_check_text(script, f"stylem/index.html inline script {index}")

    require(policy, "record.sourceStatus === 'CONFIRMED'", "confirmed product eligibility")
    require(policy, "record.status === 'PUBLISHED'", "published yarn eligibility")
    require(policy, "function safeProduct", "safe product projection")
    require(policy, "function safeYarn", "safe yarn projection")
    require(policy, "PORTAL_KEY = 'kc_customer_portal_STYLEM_v1'", "isolated STYLEM snapshot key")
    require(policy, "REQUESTS_KEY = 'kc_customer_requests_v1'", "customer request return key")

    safe_product = function_block(policy, "safeProduct")
    safe_yarn = function_block(policy, "safeYarn")
    for forbidden_field in ("brandMemo", "research", "developmentHypothesis"):
        forbid(safe_product, forbidden_field, f"internal product field in customer projection: {forbidden_field}")
    for forbidden_field in ("price", "moq", "leadTime", "notes"):
        forbid(safe_yarn, forbidden_field, f"commercial yarn field in customer projection: {forbidden_field}")

    require(admin, "grant.status==='APPROVED'", "explicit approved grant filtering")
    require(admin, "map(P.safeProduct).filter(Boolean)", "safe product snapshot publishing")
    require(admin, "map(P.safeYarn).filter(Boolean)", "safe yarn snapshot publishing")
    require(admin, "publishSnapshot", "customer snapshot publication")
    require(admin, "previousSharing", "sharing rollback")
    require(admin, "previousPortal", "portal rollback")

    forbid(portal, "kc_independent_practical_v0_4", "direct master storage access from STYLEM portal")
    forbid(portal, "kc_customer_sharing_v1", "direct grant storage access from STYLEM portal")
    require(portal, "localStorage.getItem(P.PORTAL_KEY)", "read-only customer snapshot access")
    require(portal, "P.newRequest", "customer request creation")
    require(portal, "localStorage.setItem(P.REQUESTS_KEY", "request return storage")

    print("OK: customer sharing boundary checks passed")


if __name__ == "__main__":
    main()
