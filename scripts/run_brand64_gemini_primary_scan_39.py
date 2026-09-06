#!/usr/bin/env python3
"""Brand64 Gemini Phase A runner with a 39-brand daily confirmation quota.

The active Brand64 universe remains 64. Priority brands are attempted first, then
remaining brands are used until 39 official-source scans reach scan_status=OK.
Unneeded brands are recorded as GEMINI_NOT_REQUIRED_TODAY and are never interpreted
as no-change.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
from typing import Any, Dict, List

import run_brand64_gemini_primary_scan as base

REQUIRED_CONFIRMED = 39
NOT_REQUIRED_STATUS = "GEMINI_NOT_REQUIRED_TODAY"


def missing_artifact(root: pathlib.Path, date: str, pointer: Dict[str, Any], reason: str) -> pathlib.Path:
    path = base.attempt_path(root, date)
    artifact = {
        "format": "KC_BRAND64_GEMINI_PRIMARY_SCAN",
        "schema_version": "1.1",
        "observation_date": date,
        "generated_at_utc": base.now_utc(),
        "gemini_execution_status": "GEMINI_SCAN_MISSING",
        "active_brand_count": 64,
        "required_confirmed_brand_count": REQUIRED_CONFIRMED,
        "confirmed_brand_count": 0,
        "attempted_brand_count": 0,
        "not_required_brand_count": 0,
        "candidate_brand_count": 0,
        "candidate_delta_count": 0,
        "errors": [reason],
        "brands": [],
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True,
        "sales_quantity_estimation": "FORBIDDEN",
    }
    base.save_json(path, artifact)
    base.save_json(root / "latest.json", {
        **pointer,
        "latest_attempted_scan_date": date,
        "gemini_execution_status": "GEMINI_SCAN_MISSING",
        "artifact_path": str(path).replace("\\", "/"),
        "active_brand_count": 64,
        "required_confirmed_brand_count": REQUIRED_CONFIRMED,
        "confirmed_brand_count": 0,
        "attempted_brand_count": 0,
        "candidate_brand_count": 0,
        "errors": [reason],
    })
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    parser.add_argument("--config", default=str(base.CONFIG_PATH))
    parser.add_argument("--output-root", default=str(base.OUTPUT_ROOT))
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--required-confirmed", type=int, default=REQUIRED_CONFIRMED)
    args = parser.parse_args()

    date = args.date or base.tokyo_today()
    if date != base.tokyo_today():
        parser.error("Live Gemini scans must use today's JST date; historical scans cannot be recreated by relabeling a live scan.")
    required = args.required_confirmed
    if required < 1 or required > 64:
        parser.error("--required-confirmed must be between 1 and 64")

    config_path = pathlib.Path(args.config)
    root = pathlib.Path(args.output_root)
    config = base.load_json(config_path)
    canonical_brands = base.active_brands(config)
    brands = [b for b in canonical_brands if b.get("priority")] + [b for b in canonical_brands if not b.get("priority")]

    previous_pointer = base.pointer_state(root)
    previous_artifact = base.comparable_artifact(root, previous_pointer)
    previous_by_id = {
        str(row.get("brand_id")): row
        for row in ((previous_artifact or {}).get("brands") or [])
        if isinstance(row, dict) and row.get("brand_id")
    }

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", base.DEFAULT_MODEL)
    if not api_key:
        path = missing_artifact(root, date, previous_pointer, "GEMINI_API_KEY repository secret is not configured.")
        print(f"GEMINI_SCAN_MISSING: {path}", file=sys.stderr)
        return 2

    results: Dict[str, Dict[str, Any]] = {}
    attempted_ids = set()
    batch_logs: List[Dict[str, Any]] = []
    errors: List[str] = []
    confirmed_count = 0
    cursor = 0
    batch_index = 0
    max_batch = max(1, min(args.batch_size, 8))

    while cursor < len(brands) and confirmed_count < required:
        needed = required - confirmed_count
        size = min(max_batch, needed, len(brands) - cursor)
        batch = brands[cursor:cursor + size]
        cursor += size
        batch_index += 1
        requested = {b["brand_id"] for b in batch}
        attempted_ids.update(requested)
        try:
            response = base.call_gemini(api_key, model, base.prompt(batch, date))
            returned_ids = set()
            for row in base.validated_rows(response, batch):
                brand_id = str(row.get("brand_id") or "")
                returned_ids.add(brand_id)
                expected = next(b for b in batch if b["brand_id"] == brand_id)
                row["brand_name"] = expected["brand_name"]
                row["official_url_hints"] = expected["official_url_hints"]
                row["candidate_deltas"] = base.compare(row, previous_by_id.get(brand_id))
                row["baseline_state"] = (
                    "COMPARED_TO_PREVIOUS_GEMINI"
                    if previous_by_id.get(brand_id)
                    else "INITIAL_GEMINI_BASELINE_NO_RETROACTIVE_DIFF_ASSERTION"
                )
                results[brand_id] = row
            for brand in batch:
                if brand["brand_id"] not in returned_ids:
                    results[brand["brand_id"]] = {
                        "brand_id": brand["brand_id"],
                        "brand_name": brand["brand_name"],
                        "scan_status": "NOT_RETURNED_BY_GEMINI",
                        "official_listing_url": "",
                        "official_url_hints": brand["official_url_hints"],
                        "notes": "Gemini did not return this attempted brand.",
                        "surface_items": [],
                        "candidate_deltas": [],
                        "baseline_state": "INCOMPLETE",
                    }
            confirmed_count = sum(1 for row in results.values() if row.get("scan_status") == "OK")
            batch_logs.append({
                "batch_index": batch_index,
                "requested_brand_ids": sorted(requested),
                "confirmed_after_batch": confirmed_count,
                "metadata": response.get("_metadata", {}),
            })
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").replace(api_key, "[REDACTED]")[:1500]
            message = f"HTTPError batch {batch_index}: {exc.code} {body}"
            errors.append(message)
            batch_logs.append({"batch_index": batch_index, "requested_brand_ids": sorted(requested), "error": message})
            if exc.code in {400, 401, 403}:
                break
        except Exception as exc:
            message = f"{type(exc).__name__} batch {batch_index}: {exc}".replace(api_key, "[REDACTED]")
            errors.append(message)
            batch_logs.append({"batch_index": batch_index, "requested_brand_ids": sorted(requested), "error": message})

    not_required_ids = []
    for brand in canonical_brands:
        if brand["brand_id"] in results:
            continue
        not_required_ids.append(brand["brand_id"])
        results[brand["brand_id"]] = {
            "brand_id": brand["brand_id"],
            "brand_name": brand["brand_name"],
            "scan_status": NOT_REQUIRED_STATUS,
            "official_listing_url": "",
            "official_url_hints": brand["official_url_hints"],
            "notes": "39-brand Gemini daily quota was already satisfied or the run ended before this brand. No no-change assertion is made.",
            "surface_items": [],
            "candidate_deltas": [],
            "baseline_state": "NOT_SCANNED_NO_CHANGE_NOT_ASSERTED",
        }

    ordered = [results[b["brand_id"]] for b in canonical_brands]
    confirmed_count = sum(1 for row in ordered if row.get("scan_status") == "OK")
    source_limited_count = sum(1 for row in ordered if row.get("scan_status") in base.SOURCE_LIMIT)
    candidate_brand_count = sum(1 for row in ordered if row.get("candidate_deltas"))
    candidate_delta_count = sum(len(row.get("candidate_deltas") or []) for row in ordered)
    status = "SUCCESS" if confirmed_count >= required else "GEMINI_SCAN_INCOMPLETE"

    path = base.attempt_path(root, date)
    artifact = {
        "format": "KC_BRAND64_GEMINI_PRIMARY_SCAN",
        "schema_version": "1.1",
        "observation_date": date,
        "generated_at_utc": base.now_utc(),
        "gemini_model": model,
        "gemini_execution_status": status,
        "active_brand_count": 64,
        "required_confirmed_brand_count": required,
        "confirmed_brand_count": confirmed_count,
        "attempted_brand_count": len(attempted_ids),
        "not_required_brand_count": len(not_required_ids),
        "not_required_brand_ids": not_required_ids,
        "source_limited_brand_count": source_limited_count,
        "candidate_brand_count": candidate_brand_count,
        "candidate_delta_count": candidate_delta_count,
        "errors": errors,
        "previous_comparable_gemini_observation_date": (previous_artifact or {}).get("observation_date"),
        "historical_gap_policy": "DO_NOT_FABRICATE_NO_CHANGE_FOR_DATES_WITHOUT_GEMINI_ARTIFACTS",
        "non_scanned_policy": "GEMINI_NOT_REQUIRED_TODAY_IS_NOT_NO_CHANGE",
        "batches": batch_logs,
        "brands": ordered,
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True,
        "sales_quantity_estimation": "FORBIDDEN",
    }
    base.save_json(path, artifact)

    pointer = {
        **previous_pointer,
        "latest_attempted_scan_date": date,
        "gemini_execution_status": status,
        "artifact_path": str(path).replace("\\", "/"),
        "active_brand_count": 64,
        "required_confirmed_brand_count": required,
        "confirmed_brand_count": confirmed_count,
        "attempted_brand_count": len(attempted_ids),
        "not_required_brand_count": len(not_required_ids),
        "source_limited_brand_count": source_limited_count,
        "candidate_brand_count": candidate_brand_count,
        "candidate_delta_count": candidate_delta_count,
        "errors": errors,
        "phase_b_rule": "ChatGPT verifies only candidate_deltas from OK Gemini brands; non-scanned and source-limited brands are not treated as no-change.",
    }
    if status == "SUCCESS":
        pointer["latest_comparable_scan_date"] = date
        pointer["latest_comparable_artifact_path"] = str(path).replace("\\", "/")
        pointer["latest_successful_scan_date"] = date
        pointer["latest_successful_artifact_path"] = str(path).replace("\\", "/")
    base.save_json(root / "latest.json", pointer)

    print(json.dumps({
        "status": status,
        "date": date,
        "active_brand_count": 64,
        "required_confirmed_brand_count": required,
        "confirmed_brand_count": confirmed_count,
        "attempted_brand_count": len(attempted_ids),
        "not_required_brand_count": len(not_required_ids),
        "source_limited_brand_count": source_limited_count,
        "candidate_brand_count": candidate_brand_count,
        "candidate_delta_count": candidate_delta_count,
        "artifact_path": str(path).replace("\\", "/"),
    }, ensure_ascii=False))
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
