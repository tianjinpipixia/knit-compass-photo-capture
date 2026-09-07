#!/usr/bin/env python3
"""Free-tier-safe Gemini MD pass over Knit Compass Brand64 official-source evidence.

The no-key direct collector fetches official sites first. This runner then asks Gemini
Flash-Lite to inspect a small set of official URLs with URL Context only (no Google
Search grounding), in paced batches, until 39 brands are confirmed or the candidate
pool is exhausted. HTTP 429 is retried once after a cooldown; a second 429 aborts the
run so the workflow never burns quota by hammering all remaining batches.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_CONFIG = ROOT / "config/brand64-free-direct-sources.json"
DIRECT_ROOT = ROOT / "data/brand-md-monitoring/direct-scans"
OUT_ROOT = ROOT / "data/brand-md-monitoring/gemini-md"
DEFAULT_MODEL = os.environ.get("GEMINI_MD_MODEL", "gemini-2.5-flash-lite")
REQUIRED_CONFIRMED = 39
DEFAULT_BATCH_SIZE = 13
DEFAULT_MAX_BATCHES = 5
DEFAULT_COOLDOWN_SECONDS = 65
MAX_SIGNALS_PER_BRAND = 5

PRIORITY_IDS = [
    "BR-00065", "BR-00066", "BR-00067", "BR-00068", "BR-00069",
    "BR-00070", "BR-00071", "BR-00072", "BR-00073", "BR-00074",
    "BR-00075", "BR-00076", "BR-00006", "BR-00051", "BR-00005", "BR-00004",
]
ALLOWED_STATUS = {"OK", "SOURCE_ACCESS_LIMITED", "SOURCE_OFFLINE", "OFFICIAL_SOURCE_NOT_FOUND"}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_jst() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()


def read_json(path: pathlib.Path, fallback: Any = None) -> Any:
    if not path.exists():
        if fallback is not None:
            return fallback
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def first_entry_url(meta: Dict[str, Any]) -> str:
    for value in meta.get("entry_urls", []):
        if isinstance(value, str) and value.startswith("https://"):
            return value
    return ""


def direct_quality(row: Dict[str, Any]) -> Tuple[int, int, int]:
    date_ok = int(row.get("observed_date") == today_jst())
    products = sum(
        1 for item in row.get("surface_items", [])
        if isinstance(item, dict) and item.get("scope_status") == "BRAND_AND_KNIT_PATH_MATCHED"
    )
    sources = len(row.get("sources", []))
    return date_ok, products, sources


def select_candidates(sources: Dict[str, Any], coverage: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    priority_order = {bid: idx for idx, bid in enumerate(PRIORITY_IDS)}
    rows: List[Dict[str, Any]] = []
    for bid, meta in sources.items():
        url = first_entry_url(meta)
        if not url:
            continue
        direct = coverage.get(bid, {}) if isinstance(coverage, dict) else {}
        quality = direct_quality(direct)
        items = []
        for item in direct.get("surface_items", [])[:8]:
            if not isinstance(item, dict):
                continue
            items.append({
                "product_name": str(item.get("product_name") or "")[:180],
                "product_url": str(item.get("product_url") or ""),
                "display_price": str(item.get("display_price") or "")[:80],
                "status_labels": [str(x)[:60] for x in (item.get("status_labels") or [])[:6]],
            })
        rows.append({
            "brand_id": bid,
            "brand_name": meta.get("brand_name", bid),
            "official_url": url,
            "priority": bid in priority_order,
            "priority_rank": priority_order.get(bid, 9999),
            "direct_quality": quality,
            "direct_status": direct.get("scan_status"),
            "direct_items": items,
        })
    rows.sort(key=lambda x: (
        0 if x["priority"] else 1,
        x["priority_rank"],
        -x["direct_quality"][0],
        -x["direct_quality"][1],
        -x["direct_quality"][2],
        x["brand_id"],
    ))
    return rows[:limit]


def response_schema_hint() -> str:
    return json.dumps({
        "brands": [{
            "brand_id": "BR-00000",
            "brand_name": "Brand",
            "scan_status": "OK",
            "official_url": "https://official.example/",
            "notes": "short factual note",
            "md_signals": [{
                "signal_type": "NEW|PREORDER|SALE|PRICE|COLOR|MATERIAL|FUNCTION|DESIGN|RESTOCK|SOLD_OUT|RANKING|PROMOTION|SEASON|CATEGORY|OTHER",
                "product_name": "",
                "product_url": "",
                "observed_text": "short official wording or concise factual paraphrase",
                "value": "",
            }],
        }]
    }, ensure_ascii=False)


def prompt(batch: List[Dict[str, Any]], date: str) -> str:
    lines = [
        "You are Gemini Phase A for Knit Compass Brand64 women's-knit MD monitoring.",
        f"Observation date: {date} (Japan).",
        "Use ONLY the official URLs supplied below and URL Context. Do not use Google Search and do not infer facts from non-official sites.",
        "Return exactly one row for every supplied brand_id.",
        "scan_status must be OK only when you successfully inspected the supplied official URL and can identify the correct brand context; otherwise use SOURCE_ACCESS_LIMITED, SOURCE_OFFLINE, or OFFICIAL_SOURCE_NOT_FOUND.",
        f"For each OK brand, collect up to {MAX_SIGNALS_PER_BRAND} useful current MD signals visible on the official surface: new/preorder/sale/price/color/material/function/design/restock/sold-out/ranking/promotion/season/category information.",
        "Do not invent product codes, composition, launch dates, ranking, functions, colors, or sales quantity. Empty is allowed when not visible.",
        "The direct collector snapshot below is supporting evidence from the same official ecosystem; it may help identify products but does not override the URL Context evidence.",
        "Output JSON only, no markdown. Shape example: " + response_schema_hint(),
        "Brands:",
    ]
    for row in batch:
        lines.append(json.dumps({
            "brand_id": row["brand_id"],
            "brand_name": row["brand_name"],
            "official_url": row["official_url"],
            "direct_status": row.get("direct_status"),
            "direct_items": row.get("direct_items", []),
        }, ensure_ascii=False))
    return "\n".join(lines)


def clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


class QuotaExhausted(RuntimeError):
    pass


def call_gemini(api_key: str, model: str, text: str, *, retry_429_seconds: int) -> Dict[str, Any]:
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "tools": [{"url_context": {}}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
        },
    }
    for attempt in (1, 2):
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                raw = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:3000]
            if exc.code != 429:
                raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
            if attempt == 2:
                raise QuotaExhausted("Gemini quota still exhausted after one cooldown retry: " + body) from exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                wait = max(retry_429_seconds, int(float(retry_after))) if retry_after else retry_429_seconds
            except (TypeError, ValueError):
                wait = retry_429_seconds
            print(f"Gemini 429 received; cooling down {wait}s before one retry.", file=sys.stderr, flush=True)
            time.sleep(wait)
    candidates = raw.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    finish = candidates[0].get("finishReason")
    if finish not in (None, "STOP"):
        raise RuntimeError("Gemini response did not finish normally: " + str(finish))
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    output = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict))
    parsed = json.loads(clean_json_text(output))
    if not isinstance(parsed, dict) or not isinstance(parsed.get("brands"), list):
        raise ValueError("Gemini output must contain a brands array")
    return {
        "parsed": parsed,
        "usage_metadata": raw.get("usageMetadata"),
        "url_context_metadata": (candidates[0] or {}).get("urlContextMetadata"),
    }


def validate_rows(response: Dict[str, Any], batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    expected = {row["brand_id"]: row for row in batch}
    accepted: Dict[str, Dict[str, Any]] = {}
    for raw in response.get("brands", []):
        if not isinstance(raw, dict):
            continue
        bid = str(raw.get("brand_id") or "")
        if bid not in expected or bid in accepted:
            continue
        status = str(raw.get("scan_status") or "")
        if status not in ALLOWED_STATUS:
            status = "SOURCE_ACCESS_LIMITED"
        signals = []
        for signal in (raw.get("md_signals") or [])[:MAX_SIGNALS_PER_BRAND]:
            if not isinstance(signal, dict):
                continue
            signals.append({
                "signal_type": str(signal.get("signal_type") or "OTHER")[:80],
                "product_name": str(signal.get("product_name") or "")[:240],
                "product_url": str(signal.get("product_url") or "")[:1000],
                "observed_text": str(signal.get("observed_text") or "")[:500],
                "value": str(signal.get("value") or "")[:240],
            })
        accepted[bid] = {
            "brand_id": bid,
            "brand_name": expected[bid]["brand_name"],
            "scan_status": status,
            "official_url": expected[bid]["official_url"],
            "notes": str(raw.get("notes") or "")[:500],
            "md_signals": signals if status == "OK" else [],
            "direct_status": expected[bid].get("direct_status"),
            "direct_item_count_in_prompt": len(expected[bid].get("direct_items", [])),
        }
    for bid, expected_row in expected.items():
        if bid not in accepted:
            accepted[bid] = {
                "brand_id": bid,
                "brand_name": expected_row["brand_name"],
                "scan_status": "SOURCE_ACCESS_LIMITED",
                "official_url": expected_row["official_url"],
                "notes": "Gemini did not return a validated row for this requested brand.",
                "md_signals": [],
                "direct_status": expected_row.get("direct_status"),
                "direct_item_count_in_prompt": len(expected_row.get("direct_items", [])),
            }
    return [accepted[row["brand_id"]] for row in batch]


def chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--required-confirmed", type=int, default=REQUIRED_CONFIRMED)
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    ap.add_argument("--max-batches", type=int, default=DEFAULT_MAX_BATCHES)
    ap.add_argument("--cooldown-seconds", type=int, default=DEFAULT_COOLDOWN_SECONDS)
    ap.add_argument("--output-root", default=str(OUT_ROOT))
    args = ap.parse_args()

    date = args.date or today_jst()
    if date != today_jst():
        ap.error("Live Gemini verification must use today's JST date")
    if not 1 <= args.required_confirmed <= 64:
        ap.error("--required-confirmed must be 1..64")
    batch_size = max(1, min(args.batch_size, 19))
    max_batches = max(1, min(args.max_batches, 5))

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_SCAN_MISSING: GEMINI_API_KEY is not configured", file=sys.stderr)
        return 2
    model = os.environ.get("GEMINI_MD_MODEL", DEFAULT_MODEL)

    direct_latest = read_json(DIRECT_ROOT / "latest.json")
    if direct_latest.get("observed_date") != date:
        print("GEMINI_SCAN_INCOMPLETE: today's direct official-source snapshot is unavailable", file=sys.stderr)
        return 1
    sources = read_json(SOURCE_CONFIG).get("brands", {})
    coverage = read_json(DIRECT_ROOT / "coverage-state.json", {})
    candidate_limit = min(64, batch_size * max_batches)
    candidates = select_candidates(sources, coverage, candidate_limit)

    all_rows: List[Dict[str, Any]] = []
    batch_logs: List[Dict[str, Any]] = []
    errors: List[str] = []
    quota_exhausted = False

    for batch_index, batch in enumerate(chunks(candidates, batch_size), start=1):
        if batch_index > max_batches:
            break
        confirmed = sum(row.get("scan_status") == "OK" for row in all_rows)
        if confirmed >= args.required_confirmed:
            break
        try:
            result = call_gemini(
                api_key,
                model,
                prompt(batch, date),
                retry_429_seconds=args.cooldown_seconds,
            )
            rows = validate_rows(result["parsed"], batch)
            all_rows.extend(rows)
            batch_logs.append({
                "batch_index": batch_index,
                "brand_ids": [row["brand_id"] for row in batch],
                "confirmed_in_batch": sum(row["scan_status"] == "OK" for row in rows),
                "usage_metadata": result.get("usage_metadata"),
                "url_context_metadata": result.get("url_context_metadata"),
            })
        except QuotaExhausted as exc:
            quota_exhausted = True
            errors.append(str(exc)[:3000])
            batch_logs.append({
                "batch_index": batch_index,
                "brand_ids": [row["brand_id"] for row in batch],
                "error": "QUOTA_EXHAUSTED_AFTER_SINGLE_RETRY",
            })
            break
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}"[:3000])
            batch_logs.append({
                "batch_index": batch_index,
                "brand_ids": [row["brand_id"] for row in batch],
                "error": f"{type(exc).__name__}: {exc}"[:1000],
            })
        confirmed = sum(row.get("scan_status") == "OK" for row in all_rows)
        if confirmed < args.required_confirmed and batch_index < max_batches:
            time.sleep(args.cooldown_seconds)

    confirmed_count = sum(row.get("scan_status") == "OK" for row in all_rows)
    signal_count = sum(len(row.get("md_signals") or []) for row in all_rows)
    signal_brands = sum(bool(row.get("md_signals")) for row in all_rows)
    status = "SUCCESS" if confirmed_count >= args.required_confirmed else "GEMINI_SCAN_INCOMPLETE"

    out_root = pathlib.Path(args.output_root)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    artifact_path = out_root / date / f"gemini-md-{stamp}.json"
    artifact = {
        "format": "KC_BRAND64_GEMINI_MD_FREE_TIER",
        "schema_version": "1.0",
        "observation_date": date,
        "generated_at_utc": now_utc(),
        "gemini_model": model,
        "gemini_execution_status": status,
        "free_tier_strategy": {
            "google_search_grounding": False,
            "url_context_only": True,
            "batch_size": batch_size,
            "max_batches": max_batches,
            "cooldown_seconds": args.cooldown_seconds,
            "retry_429_once": True,
            "abort_after_second_429": True,
        },
        "active_brand_count": 64,
        "required_confirmed_brand_count": args.required_confirmed,
        "attempted_brand_count": len(all_rows),
        "confirmed_brand_count": confirmed_count,
        "md_signal_brand_count": signal_brands,
        "md_signal_count": signal_count,
        "quota_exhausted": quota_exhausted,
        "direct_snapshot": {
            "observed_date": direct_latest.get("observed_date"),
            "attempted_brand_count": direct_latest.get("attempted_brand_count"),
            "product_observed_brand_count": direct_latest.get("product_observed_brand_count"),
            "product_count": direct_latest.get("product_count"),
        },
        "errors": errors,
        "batches": batch_logs,
        "brands": all_rows,
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True,
        "sales_quantity_estimation": "FORBIDDEN",
        "phase_b_rule": "ChatGPT verifies official individual product pages only for candidate/MD-signal brands; unconfirmed brands are not no-change.",
    }
    save_json(artifact_path, artifact)
    latest = {
        "latest_attempted_scan_date": date,
        "gemini_execution_status": status,
        "artifact_path": str(artifact_path).replace("\\", "/"),
        "required_confirmed_brand_count": args.required_confirmed,
        "confirmed_brand_count": confirmed_count,
        "attempted_brand_count": len(all_rows),
        "md_signal_brand_count": signal_brands,
        "md_signal_count": signal_count,
        "quota_exhausted": quota_exhausted,
        "errors": errors,
    }
    if status == "SUCCESS":
        latest["latest_successful_scan_date"] = date
        latest["latest_successful_artifact_path"] = str(artifact_path).replace("\\", "/")
    save_json(out_root / "latest.json", latest)
    print(json.dumps(latest, ensure_ascii=False))
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
