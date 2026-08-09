#!/usr/bin/env python3
"""Validate monthly official-listing observations and publish-held MD proposal linkage."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "brand-intelligence" / "app.html"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def main() -> None:
    html = APP.read_text(encoding="utf-8")
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)
    if not scripts:
        fail("V04 app has no inline script")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(scripts[-1])
        path = Path(handle.name)
    try:
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            fail(f"V04 JavaScript syntax error: {result.stderr.strip()}")
    finally:
        path.unlink(missing_ok=True)

    for token, label in (
        ('data-page="monthly-md"', "monthly MD navigation"),
        ('id="monthlyObservationForm"', "observation form"),
        ('id="mdProposalForm"', "MD proposal form"),
        ("monthlyObservations:[]", "observation state"),
        ("mdProposals:[]", "MD proposal state"),
        ("salesQuantityStatus", "sales availability state"),
        ("salesQuantity=null", "unavailable sales null storage"),
        ("salesQuantityEvidence", "sales evidence reference"),
        ("method:'OFFICIAL_LISTING_MANUAL_COUNT'", "manual listing count method"),
        ("estimationPolicy:'NO_ESTIMATION'", "observation no-estimation policy"),
        ("estimationPolicy:'NO_SALES_ESTIMATION'", "proposal no-estimation policy"),
        ("publicationStatus:'HOLD'", "publish hold"),
        ("observationSnapshot", "observation-to-proposal linkage"),
        ("monthly_observations:state.monthlyObservations", "server export observations"),
        ("md_proposals:state.mdProposals", "server export proposals"),
    ):
        require(html, token, label)
    if "estimatedSalesQuantity" in html or "salesQuantityEstimate" in html:
        fail("sales quantity estimation field is forbidden")
    if '<option value="NOT_AVAILABLE">取得不可（推定しない）</option>' not in html:
        fail("NOT_AVAILABLE must be the default sales quantity state")
    if '<option value="EVIDENCE_PROVIDED">根拠資料あり</option>' not in html:
        fail("evidence-provided sales quantity state is missing")
    if html.find('value="NOT_AVAILABLE"') > html.find('value="EVIDENCE_PROVIDED"'):
        fail("NOT_AVAILABLE must be the first sales quantity option")

    print("OK: monthly listing observation → MD proposal linkage keeps sales unavailable unless evidenced and publish held")


if __name__ == "__main__":
    main()
