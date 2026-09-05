#!/usr/bin/env python3
"""Knit Compass Brand64 Phase A Gemini primary scan.

Reads the canonical active 64-brand set, scans official women's-knit surfaces with
Gemini (known official URLs first, Google Search fallback), saves a surface snapshot,
and compares it with the previous Gemini attempt. Missing/inaccessible sources are
never converted into "no change".
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from typing import Any, Dict, Iterable, List, Optional, Tuple

CONFIG_PATH = pathlib.Path("config/brand64-active-brands.json")
OUTPUT_ROOT = pathlib.Path("data/brand-md-monitoring/gemini-primary-scans")
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
SOURCE_LIMIT = {
    "SOURCE_ACCESS_LIMITED",
    "SOURCE_OFFLINE",
    "URL_MISSING",
    "OFFICIAL_SOURCE_NOT_FOUND",
    "NOT_RETURNED_BY_GEMINI",
    "SOURCE_EVIDENCE_MISSING",
}
ALLOWED_SCAN_STATUSES = {"OK", "SOURCE_ACCESS_LIMITED", "SOURCE_OFFLINE", "URL_MISSING", "OFFICIAL_SOURCE_NOT_FOUND"}
FOCUS_BRANDS = {
    "ZARA", "SNIDEL", "GLOBAL WORK", "NATURAL BEAUTY BASIC", "VIS", "ROPÉ PICNIC",
    "GALLARDAGALANTE", "WHIM GAZETTE", "LOUNGEDRESS", "RIVE DROITE", "DOUDOU",
    "SHENERY", "UN DIX CORS", "LA BOUTIQUE BONBON", "NATURAL COUTURE", "DISCOAT",
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def tokyo_today() -> str:
    jst = dt.timezone(dt.timedelta(hours=9))
    return dt.datetime.now(jst).date().isoformat()


def load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def urls(values: Iterable[Any]) -> List[str]:
    out, seen = [], set()
    for value in values:
        if isinstance(value, str) and value.startswith("http") and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def known_url_map(config: Dict[str, Any]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    pal = config.get("pal_group") or {}
    common = pal.get("common_knit_entry_url")
    for brand_id, meta in (pal.get("brands") or {}).items():
        if isinstance(meta, dict):
            result[brand_id] = urls([meta.get("official_url"), common])
    for group_key in ("global_signal_brands", "japan_signal_brands"):
        for brand_id, meta in (config.get(group_key) or {}).items():
            if not isinstance(meta, dict):
                continue
            found = [v for k, v in meta.items() if isinstance(v, str) and (k.endswith("_url") or k == "official_url")]
            if found:
                result[brand_id] = urls(result.get(brand_id, []) + found)
    return result


def active_brands(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    active = config.get("active_brands")
    if not isinstance(active, dict):
        raise ValueError("active_brands must be an object")
    hint_map = known_url_map(config)
    rows = [
        {
            "brand_id": str(brand_id),
            "brand_name": str(name),
            "official_url_hints": hint_map.get(str(brand_id), []),
            "priority": str(name).upper() in FOCUS_BRANDS,
        }
        for brand_id, name in active.items()
    ]
    if len(rows) != 64:
        raise ValueError(f"Expected 64 active brands, found {len(rows)}")
    return rows


def chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "brands": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "brand_id": {"type": "string"},
                        "brand_name": {"type": "string"},
                        "scan_status": {"type": "string"},
                        "official_listing_url": {"type": "string"},
                        "notes": {"type": "string"},
                        "surface_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_name": {"type": "string"},
                                    "product_url": {"type": "string"},
                                    "display_price": {"type": "string"},
                                    "status_labels": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["product_name", "product_url", "display_price", "status_labels"],
                            },
                        },
                    },
                    "required": ["brand_id", "brand_name", "scan_status", "official_listing_url", "notes", "surface_items"],
                },
            }
        },
        "required": ["brands"],
    }


def prompt(batch: List[Dict[str, Any]], date: str) -> str:
    lines = [
        "You are Gemini Phase A for Knit Compass Brand64 women's knit monitoring.",
        f"Observation date: {date}.",
        "Check ONLY official brand sites or official EC pages.",
        "This is a lightweight listing-page scan, not deep product verification.",
        "Use supplied official URL hints first. If none are supplied, use Google Search to locate an official women's knit listing or official brand EC page.",
        "Return exactly one record per supplied brand_id.",
        "scan_status must be one of OK, SOURCE_ACCESS_LIMITED, SOURCE_OFFLINE, URL_MISSING, OFFICIAL_SOURCE_NOT_FOUND.",
        "If access is limited, do not infer no-change.",
        "For OK sources capture up to 20 visible women's knit items: product_name, product_url, display_price, status_labels (NEW/PREORDER/SALE/SOLD_OUT etc.).",
        "Do not invent product codes, composition, functions, colors, sales dates, or sales quantity.",
        "Return JSON only and preserve brand_id exactly. Use this schema: " + json.dumps(schema()),
        "Brands:",
    ]
    for b in batch:
        hints = " | ".join(b["official_url_hints"]) or "NONE"
        lines.append(f"- {b['brand_id']} | {b['brand_name']} | priority={b['priority']} | official_url_hints={hints}")
    return "\n".join(lines)


def call_gemini(api_key: str, model: str, text: str) -> Dict[str, Any]:
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "tools": [{"googleSearch": {}}, {"urlContext": {}}],
        "generationConfig": {
            "temperature": 0.1,
        },
    }
    # Structured output combined with tools is supported by the Gemini 3 family.
    # Gemini 2.5 still uses Search/URL Context; parse and validate its JSON locally.
    if model.startswith("gemini-3"):
        payload["generationConfig"].update(responseMimeType="application/json", responseSchema=schema())
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        raw = json.loads(response.read().decode("utf-8"))
    candidates = raw.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    if candidates[0].get("finishReason") not in (None, "STOP"):
        raise RuntimeError("Gemini response was not completed: " + str(candidates[0].get("finishReason")))
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    body = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))
    if not body.strip():
        raise RuntimeError("Gemini returned no text payload")
    body = re.sub(r"^```(?:json)?\s*|\s*```$", "", body.strip(), flags=re.I)
    parsed = json.loads(body)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("brands"), list):
        raise ValueError("Gemini must return a brands array")
    parsed["_metadata"] = {
        "usage_metadata": raw.get("usageMetadata"),
        "url_context_metadata": (candidates[0] or {}).get("urlContextMetadata"),
        "grounding_metadata": (candidates[0] or {}).get("groundingMetadata"),
    }
    return parsed


def http_url(value: Any) -> bool:
    try:
        url = urlsplit(str(value or ""))
        return url.scheme in {"http", "https"} and bool(url.hostname) and not url.username and not url.password
    except ValueError:
        return False


def validated_rows(response: Dict[str, Any], batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    requested = {b["brand_id"] for b in batch}
    seen, accepted = set(), []
    metadata = response.get("_metadata") or {}
    retrieved = [x.get("retrievedUrl") for x in (metadata.get("url_context_metadata") or {}).get("urlMetadata", [])
                 if x.get("urlRetrievalStatus") == "URL_RETRIEVAL_STATUS_SUCCESS"]
    retrieved += [x.get("web", {}).get("uri") for x in (metadata.get("grounding_metadata") or {}).get("groundingChunks", [])]
    evidence_hosts = {urlsplit(url).hostname for url in retrieved if http_url(url)}
    for raw in response.get("brands", []):
        if not isinstance(raw, dict):
            raise ValueError("Invalid Gemini brand record")
        row = dict(raw)
        brand_id = row.get("brand_id")
        if brand_id not in requested or brand_id in seen:
            raise ValueError("Unexpected or duplicate brand_id in Gemini response")
        seen.add(brand_id)
        if row.get("scan_status") not in ALLOWED_SCAN_STATUSES:
            raise ValueError("Unsupported Gemini scan_status")
        if not isinstance(row.get("surface_items"), list):
            raise ValueError("surface_items must be an array")
        for item in row["surface_items"]:
            if not isinstance(item, dict) or not isinstance(item.get("product_name"), str) or not http_url(item.get("product_url")):
                raise ValueError("Invalid Gemini surface item")
            if not isinstance(item.get("display_price"), str) or not isinstance(item.get("status_labels"), list) or not all(isinstance(x, str) for x in item["status_labels"]):
                raise ValueError("Invalid Gemini item price or labels")
        if row["scan_status"] == "OK":
            if not http_url(row.get("official_listing_url")):
                raise ValueError("OK requires an official listing URL")
            host = urlsplit(row["official_listing_url"]).hostname
            row["retrieved_source_urls"] = [url for url in retrieved if http_url(url) and urlsplit(url).hostname == host]
            if host not in evidence_hosts:
                row["scan_status"] = "SOURCE_EVIDENCE_MISSING"
                row["notes"] = "Gemini did not return retrieval evidence for this listing host. Phase A remains incomplete."
        accepted.append(row)
    return accepted


def item_key(item: Dict[str, Any]) -> str:
    url = str(item.get("product_url") or "").strip()
    return "url:" + url if url else "name:" + str(item.get("product_name") or "").strip().lower()


def labels(item: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple(sorted(str(x).strip().upper() for x in (item.get("status_labels") or []) if str(x).strip()))


def compare(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if current.get("scan_status") != "OK" or not previous or previous.get("scan_status") != "OK":
        return []
    cur = {item_key(x): x for x in (current.get("surface_items") or [])}
    old = {item_key(x): x for x in (previous.get("surface_items") or [])}
    delta: List[Dict[str, Any]] = []
    for key, item in cur.items():
        before = old.get(key)
        if before is None:
            delta.append({"delta_type": "NEW_PRODUCT_CANDIDATE", "product_name": item.get("product_name", ""), "product_url": item.get("product_url", ""), "reason": "Visible now but absent from previous Gemini official-listing snapshot."})
            continue
        p_now, p_old = str(item.get("display_price") or "").strip(), str(before.get("display_price") or "").strip()
        if p_now and p_old and p_now != p_old:
            delta.append({"delta_type": "PRICE_CHANGE_CANDIDATE", "product_name": item.get("product_name", ""), "product_url": item.get("product_url", ""), "reason": f"Listing price changed: {p_old} -> {p_now}."})
        l_now, l_old = labels(item), labels(before)
        if l_now != l_old:
            all_labels = set(l_now) | set(l_old)
            dtype = "LISTING_STATUS_CHANGE_CANDIDATE"
            if any("SALE" in x for x in all_labels):
                dtype = "SALE_STATUS_CHANGE_CANDIDATE"
            elif any("PREORDER" in x or "予約" in x for x in all_labels):
                dtype = "RESERVATION_STATUS_CHANGE_CANDIDATE"
            delta.append({"delta_type": dtype, "product_name": item.get("product_name", ""), "product_url": item.get("product_url", ""), "reason": f"Status labels changed: {list(l_old)} -> {list(l_now)}."})
    for key, before in old.items():
        if key not in cur:
            delta.append({"delta_type": "LISTING_PRESENCE_CHANGE_CANDIDATE", "product_name": before.get("product_name", ""), "product_url": before.get("product_url", ""), "reason": "Previously visible but absent from current listing surface; Phase B must verify ranking movement, sold-out, or removal."})
    return delta


def pointer_state(root: pathlib.Path) -> Dict[str, Any]:
    path = root / "latest.json"
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except Exception:
        return {}


def comparable_artifact(root: pathlib.Path, pointer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    value = pointer.get("latest_comparable_artifact_path") or pointer.get("latest_successful_artifact_path")
    if not value:
        return None
    path = pathlib.Path(value)
    if not path.exists():
        return None
    try:
        return load_json(path)
    except Exception:
        return None


def attempt_path(root: pathlib.Path, date: str) -> pathlib.Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return root / date[:4] / date[5:7] / f"brand64_gemini_primary_scan_{date}_{stamp}.json"


def write_missing(root: pathlib.Path, date: str, pointer: Dict[str, Any], count: int, reason: str) -> pathlib.Path:
    path = attempt_path(root, date)
    artifact = {
        "format": "KC_BRAND64_GEMINI_PRIMARY_SCAN", "schema_version": "1.0",
        "observation_date": date, "generated_at_utc": now_utc(),
        "gemini_execution_status": "GEMINI_SCAN_MISSING", "expected_brand_count": count,
        "returned_brand_count": 0, "source_limited_brand_count": 0,
        "candidate_brand_count": 0, "candidate_delta_count": 0,
        "missing_brand_ids": [], "errors": [reason], "brands": [],
        "publication_status": "PUBLISH_HOLD", "human_review_required": True,
        "sales_quantity_estimation": "FORBIDDEN",
    }
    save_json(path, artifact)
    save_json(root / "latest.json", {
        **pointer,
        "latest_attempted_scan_date": date,
        "gemini_execution_status": "GEMINI_SCAN_MISSING",
        "artifact_path": str(path).replace("\\", "/"),
        "expected_brand_count": count, "returned_brand_count": 0,
        "candidate_brand_count": 0, "errors": [reason],
    })
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--config", default=str(CONFIG_PATH))
    ap.add_argument("--output-root", default=str(OUTPUT_ROOT))
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    date = args.date or tokyo_today()
    if date != tokyo_today():
        ap.error("Live Gemini scans must use today's JST date; historical observations cannot be recreated by relabeling a live scan.")
    root = pathlib.Path(args.output_root)
    config = load_json(pathlib.Path(args.config))
    brands = active_brands(config)
    previous_pointer = pointer_state(root)
    previous_artifact = comparable_artifact(root, previous_pointer)
    previous_by_id = {str(x.get("brand_id")): x for x in ((previous_artifact or {}).get("brands") or []) if isinstance(x, dict) and x.get("brand_id")}

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    if not api_key:
        path = write_missing(root, date, previous_pointer, len(brands), "GEMINI_API_KEY repository secret is not configured.")
        print(f"GEMINI_SCAN_MISSING: {path}", file=sys.stderr)
        return 2

    results: Dict[str, Dict[str, Any]] = {}
    batch_logs, errors = [], []
    batch_size = max(1, min(args.batch_size, 8))
    for index, batch in enumerate(chunks(brands, batch_size), start=1):
        requested = {b["brand_id"] for b in batch}
        try:
            response = call_gemini(api_key, model, prompt(batch, date))
            accepted = 0
            for row in validated_rows(response, batch):
                brand_id = str(row.get("brand_id") or "")
                if brand_id not in requested:
                    continue
                expected = next(b for b in batch if b["brand_id"] == brand_id)
                row["brand_name"] = expected["brand_name"]
                row["official_url_hints"] = expected["official_url_hints"]
                row["candidate_deltas"] = compare(row, previous_by_id.get(brand_id))
                row["baseline_state"] = "COMPARED_TO_PREVIOUS_GEMINI" if previous_by_id.get(brand_id) else "INITIAL_GEMINI_BASELINE_NO_RETROACTIVE_DIFF_ASSERTION"
                results[brand_id] = row
                accepted += 1
            batch_logs.append({"batch_index": index, "requested_brand_ids": sorted(requested), "accepted_brand_count": accepted, "metadata": response.get("_metadata", {})})
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").replace(api_key, "[REDACTED]")[:1500]
            msg = f"HTTPError batch {index}: {exc.code} {body}"
            errors.append(msg); batch_logs.append({"batch_index": index, "error": msg})
            if exc.code in {400, 401, 403}:
                break
        except Exception as exc:
            msg = f"{type(exc).__name__} batch {index}: {exc}".replace(api_key, "[REDACTED]")
            errors.append(msg); batch_logs.append({"batch_index": index, "error": msg})

    missing_ids = [b["brand_id"] for b in brands if b["brand_id"] not in results]
    for b in brands:
        if b["brand_id"] in results:
            continue
        results[b["brand_id"]] = {
            "brand_id": b["brand_id"], "brand_name": b["brand_name"],
            "scan_status": "NOT_RETURNED_BY_GEMINI", "official_listing_url": "",
            "official_url_hints": b["official_url_hints"], "notes": "Gemini did not return this brand.",
            "surface_items": [], "candidate_deltas": [], "baseline_state": "INCOMPLETE",
        }

    ordered = [results[b["brand_id"]] for b in brands]
    returned_count = len(brands) - len(missing_ids)
    limited_count = sum(1 for row in ordered if row.get("scan_status") in SOURCE_LIMIT)
    candidate_brands = sum(1 for row in ordered if row.get("candidate_deltas"))
    candidate_deltas = sum(len(row.get("candidate_deltas") or []) for row in ordered)
    status = "SUCCESS" if not errors and not missing_ids and limited_count == 0 else "GEMINI_SCAN_INCOMPLETE"

    path = attempt_path(root, date)
    artifact = {
        "format": "KC_BRAND64_GEMINI_PRIMARY_SCAN", "schema_version": "1.0",
        "observation_date": date, "generated_at_utc": now_utc(), "gemini_model": model,
        "gemini_execution_status": status, "expected_brand_count": len(brands),
        "returned_brand_count": returned_count, "source_limited_brand_count": limited_count,
        "candidate_brand_count": candidate_brands, "candidate_delta_count": candidate_deltas,
        "missing_brand_ids": missing_ids, "errors": errors,
        "previous_comparable_gemini_observation_date": (previous_artifact or {}).get("observation_date"),
        "historical_gap_policy": "DO_NOT_FABRICATE_NO_CHANGE_FOR_DATES_WITHOUT_GEMINI_ARTIFACTS",
        "batches": batch_logs, "brands": ordered,
        "publication_status": "PUBLISH_HOLD", "human_review_required": True,
        "sales_quantity_estimation": "FORBIDDEN",
    }
    save_json(path, artifact)

    pointer = {
        **previous_pointer,
        "latest_attempted_scan_date": date,
        "gemini_execution_status": status,
        "artifact_path": str(path).replace("\\", "/"),
        "expected_brand_count": len(brands), "returned_brand_count": returned_count,
        "source_limited_brand_count": limited_count, "candidate_brand_count": candidate_brands,
        "candidate_delta_count": candidate_deltas, "missing_brand_ids": missing_ids, "errors": errors,
        "phase_b_rule": "ChatGPT verifies only candidate_deltas from scan_status OK brands; source-limited brands remain unresolved.",
    }
    if status == "SUCCESS":
        pointer["latest_comparable_scan_date"] = date
        pointer["latest_comparable_artifact_path"] = str(path).replace("\\", "/")
        pointer["latest_successful_scan_date"] = date
        pointer["latest_successful_artifact_path"] = str(path).replace("\\", "/")
    save_json(root / "latest.json", pointer)

    print(json.dumps({"status": status, "date": date, "returned_brand_count": returned_count, "source_limited_brand_count": limited_count, "candidate_brand_count": candidate_brands, "candidate_delta_count": candidate_deltas, "artifact_path": str(path).replace("\\", "/")}, ensure_ascii=False))
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
