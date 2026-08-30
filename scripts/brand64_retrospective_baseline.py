#!/usr/bin/env python3
"""Gate, ingest, deduplicate, and recount Brand64 spring retrospective baselines.

This script never crawls an external site. It accepts already verified official
individual-product-page observations and only writes them after the current-day
Brand64 scan and all observation-gap recovery are complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

FORMAT = "KC_BRAND64_RETROSPECTIVE_BASELINE_LEDGER"
RECORD_SCOPE = "RETROSPECTIVE_BASELINE"
REPORT_FORMAT = "KC_BRAND64_RETROSPECTIVE_BACKFILL_REPORT"
SUMMARY_START = "<!-- KC_RETROSPECTIVE_SEASON_BACKFILL:START -->"
SUMMARY_END = "<!-- KC_RETROSPECTIVE_SEASON_BACKFILL:END -->"
UNKNOWN_MARKERS = {"", "UNKNOWN", "NOT AVAILABLE", "NOT_AVAILABLE", "N/A", "NA", "不明", "未確認"}
PERIOD_EVIDENCE_KINDS = {
    "OFFICIAL_RELEASE_DATE",
    "OFFICIAL_RESERVATION_DATE",
    "OFFICIAL_PAGE_PUBLISHED_DATE",
    "OFFICIAL_SEASON_LABEL",
}
OPTIONAL_NULL_FIELDS = ("product_code", "regular_price_jpy", "sale_price_jpy", "composition", "launch_status")
OPTIONAL_LIST_FIELDS = ("function_claims", "colors")


@dataclass(frozen=True)
class Paths:
    root: Path
    monitoring_config: Path
    active_config: Path
    latest: Path
    monitoring_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> "Paths":
        resolved = root.resolve()
        monitoring_dir = resolved / "data/brand-md-monitoring"
        return cls(
            root=resolved,
            monitoring_config=resolved / "config/brand64-md-monitoring.json",
            active_config=resolved / "config/brand64-active-brands.json",
            latest=monitoring_dir / "latest.json",
            monitoring_dir=monitoring_dir,
        )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def repository_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    path.relative_to(root.resolve())
    return path


def canonical_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parts = urlsplit(raw)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return ""
    path = re.sub(r"/+", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def normalized_code(value: Any) -> str:
    raw = str(value or "").strip()
    return "" if raw.upper() in UNKNOWN_MARKERS else raw.upper()


def strong_keys(row: dict[str, Any]) -> list[str]:
    code = normalized_code(row.get("product_code"))
    url = canonical_url(row.get("official_url") or row.get("product_url") or row.get("source_url"))
    return [key for key in (f"code:{code}" if code else "", f"url:{url}" if url else "") if key]


def read_input(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(parsed, dict):
        parsed = parsed.get("records", [])
    if not isinstance(parsed, list) or not all(isinstance(item, dict) for item in parsed):
        raise ValueError("input must be a JSON array, a records object, or JSONL objects")
    return parsed


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def period_bounds(value: str) -> tuple[date, date]:
    start_text, end_text = value.split("/", 1)
    start = date.fromisoformat(start_text)
    end = date.fromisoformat(end_text)
    if start > end:
        raise ValueError("retrospective_period start must not exceed end")
    return start, end


def exact_unknown(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() in UNKNOWN_MARKERS


def validate_period_evidence(evidence: Any, period: str) -> None:
    if not isinstance(evidence, dict):
        raise ValueError("period_evidence is required")
    kind = str(evidence.get("kind") or "").strip().upper()
    value = str(evidence.get("value") or "").strip()
    if kind not in PERIOD_EVIDENCE_KINDS or not value:
        raise ValueError("period_evidence must use an allowed kind and non-empty official value")
    if kind.endswith("DATE"):
        observed = date.fromisoformat(value)
        start, end = period_bounds(period)
        if not start <= observed <= end:
            raise ValueError(f"period_evidence date {observed} is outside {period}")
    else:
        normalized = value.upper().replace(" ", "")
        if "2026" not in normalized or not any(token in normalized for token in ("SS", "SPRING", "春")):
            raise ValueError("OFFICIAL_SEASON_LABEL must explicitly identify 2026 spring/SS")


def normalize_candidate(
    raw: dict[str, Any],
    *,
    observed_date: str,
    period: str,
    accepted_source_kinds: set[str],
    active_brands: dict[str, str],
) -> dict[str, Any]:
    row = deepcopy(raw)
    brand_id = str(row.get("brand_id") or "").strip()
    brand_name = str(row.get("brand_name") or "").strip()
    if brand_id not in active_brands or active_brands[brand_id] != brand_name:
        raise ValueError(f"active Brand64 identity mismatch: {brand_id} / {brand_name}")
    if str(row.get("product_name") or "").strip().upper() in UNKNOWN_MARKERS:
        raise ValueError("product_name is required and must not be guessed")

    source_status = str(row.get("source_status") or "ONLINE").strip().upper()
    if source_status not in {"ONLINE", "SOURCE_OFFLINE"}:
        raise ValueError("source_status must be ONLINE or SOURCE_OFFLINE")
    official_url = canonical_url(row.get("official_url"))
    if not official_url:
        raise ValueError("an http(s) official individual product URL is required")
    source_kind = str(row.get("source_kind") or "").strip().upper()
    if source_kind not in accepted_source_kinds:
        raise ValueError("source_kind must identify an official individual product page")

    declared_period = str(row.get("retrospective_period") or period)
    if declared_period != period:
        raise ValueError(f"retrospective_period must be {period}")
    validate_period_evidence(row.get("period_evidence"), period)

    record_scope = str(row.get("record_scope") or row.get("observation_kind") or RECORD_SCOPE).upper()
    if record_scope != RECORD_SCOPE:
        raise ValueError(f"record_scope must be {RECORD_SCOPE}")
    if row.get("sales_quantity") not in {None, "NOT_AVAILABLE", "NOT_ESTIMATED"}:
        raise ValueError("sales quantity values or estimates are forbidden")
    if row.get("publication_status", "PUBLISH_HOLD") != "PUBLISH_HOLD":
        raise ValueError("publication_status must remain PUBLISH_HOLD")
    if row.get("human_review_required", True) is not True:
        raise ValueError("human_review_required must remain true")

    normalized: dict[str, Any] = {
        "format": "KC_BRAND64_PRODUCT_BASELINE",
        "schema_version": "1.5",
        "observation_kind": RECORD_SCOPE,
        "record_scope": RECORD_SCOPE,
        "retrospective_period": period,
        "backfill_observation_date": observed_date,
        "first_backfill_observation_date": observed_date,
        "confirmed_at": str(row.get("confirmed_at") or "").strip(),
        "last_checked_at": str(row.get("last_checked_at") or row.get("confirmed_at") or "").strip(),
        "brand_id": brand_id,
        "brand_name": brand_name,
        "product_name": str(row.get("product_name") or "").strip(),
        "official_url": official_url,
        "source_kind": source_kind,
        "source_status": source_status,
        "period_evidence": {
            "kind": str(row["period_evidence"]["kind"]).strip().upper(),
            "value": str(row["period_evidence"]["value"]).strip(),
        },
        "sales_quantity": "NOT_AVAILABLE",
        "sales_quantity_estimation": "FORBIDDEN",
        "data_quality_status": "REVIEW_REQUIRED",
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True,
    }
    for field in OPTIONAL_NULL_FIELDS:
        value = row.get(field)
        if exact_unknown(value):
            value = None
        if field.endswith("_jpy") and value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{field} must be a non-negative number or null")
        elif value is not None and not isinstance(value, str):
            raise ValueError(f"{field} must be a string or null")
        normalized[field] = value
    for field in OPTIONAL_LIST_FIELDS:
        value = row.get(field)
        if value is not None and (not isinstance(value, list) or not all(isinstance(item, str) for item in value)):
            raise ValueError(f"{field} must be an array of official strings or null")
        normalized[field] = value
    for field in ("notes", "source_offline_at"):
        value = row.get(field)
        normalized[field] = None if exact_unknown(value) else value
    if not normalized["confirmed_at"] or not normalized["last_checked_at"]:
        raise ValueError("confirmed_at/last_checked_at are required; do not fabricate a confirmation time")
    if normalized["confirmed_at"][:10] != observed_date:
        raise ValueError("confirmed_at must belong to the first backfill observation date")
    if normalized_code(normalized.get("product_code")):
        normalized["product_code"] = normalized_code(normalized["product_code"])
    else:
        normalized["product_code"] = None
    product_identity = normalized["product_code"] or hashlib.sha1(official_url.encode("utf-8")).hexdigest()[:16].upper()
    product_identity = re.sub(r"[^A-Z0-9]+", "_", product_identity).strip("_")
    regular_price = normalized["regular_price_jpy"]
    sale_price = normalized["sale_price_jpy"]
    claims = normalized["function_claims"]
    period_evidence = normalized["period_evidence"]
    launch_status = normalized["launch_status"] or "NOT AVAILABLE"
    projected_launch_status = launch_status if "PUBLISH_HOLD" in launch_status else f"{launch_status} / PUBLISH_HOLD"
    normalized.update({
        "product_id": f"B64_RETRO_{product_identity}",
        "product_url": official_url,
        "source_type": "BRAND64_OFFICIAL_PRODUCT_PAGE",
        "season": "2026SS" if period_evidence["kind"] == "OFFICIAL_SEASON_LABEL" else "NOT AVAILABLE",
        "price": f"JPY {regular_price:g}" if regular_price is not None else "NOT AVAILABLE",
        "regular_price": f"JPY {regular_price:g}" if regular_price is not None else "NOT AVAILABLE",
        "sale_price": f"JPY {sale_price:g}" if sale_price is not None else "NOT AVAILABLE",
        "function": "; ".join(claims) if claims else "NOT AVAILABLE",
        "knit_structure": "NOT AVAILABLE",
        "category": "Women_Knit",
        "launch_status": projected_launch_status,
        "source_date": period_evidence["value"] if period_evidence["kind"].endswith("DATE") else "NOT AVAILABLE",
        "last_verified_date": normalized["last_checked_at"][:10],
        "first_seen_observation": observed_date,
        "recommended_yarn_ids": [],
        "yarn_relation_status": "OWNER_REVIEW_REQUIRED",
        "customer_share_status": "PUBLISH_HOLD",
    })
    normalized["dedupe_keys"] = {
        "product_code": normalized["product_code"],
        "official_url": normalized["official_url"],
    }
    return normalized


def readiness(
    *,
    latest: dict[str, Any],
    daily: dict[str, Any],
    run_date: str,
    policy: dict[str, Any],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    gate = policy.get("readiness", {})
    if gate.get("latest_observed_date_must_equal_run_date") and latest.get("observed_date") != run_date:
        reasons.append("LATEST_DATE_NOT_ADVANCED")
    if daily.get("observed_date") != run_date:
        reasons.append("DAILY_DATE_NOT_ADVANCED")
    if daily.get("light_check_count", daily.get("light_check_completed")) != gate.get("required_light_check_count"):
        reasons.append("CURRENT_DAY_LIGHT_SCAN_INCOMPLETE")
    if len(set(daily.get("checked_brand_ids", []))) != gate.get("required_checked_brand_count"):
        reasons.append("CURRENT_DAY_BRAND_SET_INCOMPLETE")
    gaps = sorted(set(latest.get("observation_gap_dates", [])) | set(daily.get("observation_gap_dates", [])))
    if gate.get("observation_gap_dates_must_be_empty") and gaps:
        reasons.append("UNPROCESSED_OBSERVATION_DATES_REMAIN")
    return not reasons, reasons


def existing_identity_index(paths: Paths, ledger_records: list[dict[str, Any]]) -> dict[str, list[tuple[str, int]]]:
    index: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for position, row in enumerate(ledger_records):
        for key in strong_keys(row):
            index[key].append(("ledger", position))
    for baseline_path in sorted(paths.monitoring_dir.glob("*-product-baseline-snapshots.jsonl")):
        for position, row in enumerate(load_jsonl(baseline_path)):
            for key in strong_keys(row):
                index[key].append((baseline_path.name, position))
    return index


def select_small_batch(
    candidates: list[dict[str, Any]], policy: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    priority = {brand_id: position for position, brand_id in enumerate(policy.get("priority_brand_ids", []))}
    ordered = sorted(
        enumerate(candidates),
        key=lambda pair: (priority.get(pair[1]["brand_id"], len(priority)), pair[0]),
    )
    max_total = int(policy.get("max_products_per_run", 4))
    max_per_brand = int(policy.get("max_products_per_brand_per_run", 2))
    counts: Counter[str] = Counter()
    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for _, row in ordered:
        if len(selected) >= max_total or counts[row["brand_id"]] >= max_per_brand:
            deferred.append(row)
            continue
        selected.append(row)
        counts[row["brand_id"]] += 1
    return selected, deferred


def merge_existing(previous: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(previous)
    if incoming["source_status"] == "SOURCE_OFFLINE":
        merged["source_status"] = "SOURCE_OFFLINE"
        merged["source_offline_at"] = incoming.get("source_offline_at") or incoming["last_checked_at"]
        merged["last_checked_at"] = incoming["last_checked_at"]
        merged["notes"] = incoming.get("notes") or merged.get("notes")
        return merged
    for key, value in incoming.items():
        if key in {"backfill_observation_date", "first_backfill_observation_date", "confirmed_at"}:
            continue
        if value is not None:
            merged[key] = deepcopy(value)
    merged["source_status"] = "ONLINE"
    return merged


def ledger_metrics(records: list[dict[str, Any]], observed_date: str) -> dict[str, Any]:
    by_brand = Counter(row["brand_id"] for row in records)
    run_count = sum(1 for row in records if row.get("first_backfill_observation_date") == observed_date)
    return {
        "retrospective_season_backfill_count": run_count,
        "retrospective_season_backfill_cumulative_count": len(records),
        "counts_by_brand": dict(sorted(by_brand.items())),
    }


def summary_block(period: str, metrics: dict[str, Any], ledger_path: str, report_path: str) -> str:
    return "\n".join([
        SUMMARY_START,
        "## 2026年春先遡及（当日差分とは別集計）",
        "",
        f"- 対象期間: `{period}`",
        f"- 当日春先遡及: **{metrics['retrospective_season_backfill_count']}件**",
        f"- 春先遡及累積: **{metrics['retrospective_season_backfill_cumulative_count']}件**",
        "- 実行条件: 当日64ブランド確認完了、かつ未処理日なしの場合のみ",
        "- 区分: `RETROSPECTIVE_BASELINE`（当日新規・通常の遡及候補には加算しない）",
        "- 根拠: 公式個別商品ページのみ。不明項目は推測しない",
        "- 公開境界: `PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED`",
        f"- 保存先: `{ledger_path}`",
        f"- 実データ再集計: `{report_path}`",
        SUMMARY_END,
    ])


def replace_summary_block(text: str, block: str) -> str:
    pattern = re.compile(re.escape(SUMMARY_START) + r".*?" + re.escape(SUMMARY_END), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(block, text).rstrip() + "\n"
    return text.rstrip() + "\n\n" + block + "\n"


def validate_ledger(
    ledger: dict[str, Any],
    *,
    period: str,
    accepted_source_kinds: set[str],
    active_brands: dict[str, str],
) -> None:
    if ledger.get("format") != FORMAT or ledger.get("record_scope") != RECORD_SCOPE:
        raise ValueError("invalid retrospective ledger format/scope")
    if ledger.get("retrospective_period") != period:
        raise ValueError("retrospective ledger period does not match monitoring policy")
    records = ledger.get("records", [])
    if not isinstance(records, list):
        raise ValueError("retrospective ledger records must be an array")
    seen: set[str] = set()
    for row in records:
        normalized = normalize_candidate(
            row,
            observed_date=str(row.get("first_backfill_observation_date") or row.get("backfill_observation_date") or ""),
            period=period,
            accepted_source_kinds=accepted_source_kinds,
            active_brands=active_brands,
        )
        if row.get("first_backfill_observation_date") != normalized["first_backfill_observation_date"]:
            raise ValueError("first_backfill_observation_date is required")
        if row.get("backfill_observation_date") != row.get("first_backfill_observation_date"):
            raise ValueError("backfill_observation_date must preserve the first backfill date")
        if row.get("product_url") != row.get("official_url"):
            raise ValueError("V04 product_url must preserve the official individual product URL")
        if not str(row.get("product_id") or "").startswith("B64_RETRO_"):
            raise ValueError("V04-compatible retrospective product_id is required")
        if row.get("source_type") != "BRAND64_OFFICIAL_PRODUCT_PAGE":
            raise ValueError("V04 source_type must preserve the official product-page boundary")
        for key in strong_keys(row):
            if key in seen:
                raise ValueError(f"duplicate retrospective identity: {key}")
            seen.add(key)


def execute(
    root: Path,
    *,
    run_date: str,
    input_path: Path | None = None,
    apply: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    date.fromisoformat(run_date)
    paths = Paths.from_root(root)
    monitoring = read_json(paths.monitoring_config)
    policy = monitoring["retrospective_season_backfill"]
    active = read_json(paths.active_config)["active_brands"]
    latest = read_json(paths.latest)
    daily_path = repository_path(paths.root, latest["daily_path"])
    daily = read_json(daily_path)
    summary_path = repository_path(paths.root, latest["summary_path"])
    period = policy["retrospective_period"]
    accepted_source_kinds = set(policy["accepted_source_kinds"])
    ledger_path = repository_path(paths.root, policy["ledger_path"])
    ledger = read_json(ledger_path)
    validate_ledger(ledger, period=period, accepted_source_kinds=accepted_source_kinds, active_brands=active)

    eligible, gate_reasons = readiness(latest=latest, daily=daily, run_date=run_date, policy=policy)
    if not eligible:
        if strict:
            raise RuntimeError("retrospective backfill gate closed: " + ", ".join(gate_reasons))
        return {
            "format": REPORT_FORMAT,
            "observed_date": run_date,
            "status": "SKIPPED",
            "eligible": False,
            "gate_reasons": gate_reasons,
            "accepted_count": 0,
            "updated_count": 0,
            "duplicate_existing_count": 0,
            "deferred_count": len(read_input(input_path)),
        }

    normalized_input = [
        normalize_candidate(
            row,
            observed_date=run_date,
            period=period,
            accepted_source_kinds=accepted_source_kinds,
            active_brands=active,
        )
        for row in read_input(input_path)
    ]
    unique_input: list[dict[str, Any]] = []
    input_keys: set[str] = set()
    duplicate_input_count = 0
    for row in normalized_input:
        keys = strong_keys(row)
        if any(key in input_keys for key in keys):
            duplicate_input_count += 1
            continue
        input_keys.update(keys)
        unique_input.append(row)
    selected, deferred = select_small_batch(unique_input, policy)

    records = deepcopy(ledger["records"])
    index = existing_identity_index(paths, records)
    accepted_count = 0
    updated_count = 0
    duplicate_existing_count = 0
    for row in selected:
        matches = {match for key in strong_keys(row) for match in index.get(key, [])}
        ledger_matches = {position for source, position in matches if source == "ledger"}
        outside_matches = {source for source, _ in matches if source != "ledger"}
        if len(ledger_matches) > 1:
            raise ValueError("product_code and official_url resolve to different retrospective records")
        if ledger_matches:
            position = next(iter(ledger_matches))
            records[position] = merge_existing(records[position], row)
            updated_count += 1
            continue
        if outside_matches:
            duplicate_existing_count += 1
            continue
        if row["source_status"] == "SOURCE_OFFLINE":
            raise ValueError("SOURCE_OFFLINE may only update an existing retrospective record")
        position = len(records)
        records.append(row)
        accepted_count += 1
        for key in strong_keys(row):
            index[key].append(("ledger", position))

    priority = {brand_id: position for position, brand_id in enumerate(policy.get("priority_brand_ids", []))}
    records.sort(key=lambda row: (priority.get(row["brand_id"], len(priority)), row["brand_id"], normalized_code(row.get("product_code")), row["official_url"]))
    metrics = ledger_metrics(records, run_date)
    report_path_text = policy["report_path_pattern"].format(observed_date=run_date)
    report = {
        "format": REPORT_FORMAT,
        "schema_version": "1.0",
        "observed_date": run_date,
        "status": "APPLIED" if apply else "READY_DRY_RUN",
        "eligible": True,
        "gate_reasons": [],
        "execution_order": policy["execution_order"],
        "retrospective_period": period,
        "accepted_count": accepted_count,
        "updated_count": updated_count,
        "duplicate_input_count": duplicate_input_count,
        "duplicate_existing_count": duplicate_existing_count,
        "deferred_count": len(deferred),
        **metrics,
        "ledger_path": policy["ledger_path"],
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True,
        "sales_quantity_estimation": "FORBIDDEN",
    }
    if not apply:
        return report

    ledger["records"] = records
    ledger["metrics"] = {
        "retrospective_season_backfill_cumulative_count": metrics["retrospective_season_backfill_cumulative_count"],
        "counts_by_brand": metrics["counts_by_brand"],
    }
    write_json(ledger_path, ledger)
    write_json(repository_path(paths.root, report_path_text), report)

    metric_fields = {
        "retrospective_season_backfill_count": metrics["retrospective_season_backfill_count"],
        "retrospective_season_backfill_cumulative_count": metrics["retrospective_season_backfill_cumulative_count"],
        "retrospective_period": period,
        "retrospective_season_backfill_path": policy["ledger_path"],
        "retrospective_season_backfill_report_path": report_path_text,
    }
    daily.update(metric_fields)
    latest.update(metric_fields)
    write_json(daily_path, daily)
    write_json(paths.latest, latest)
    summary = summary_path.read_text(encoding="utf-8")
    summary_path.write_text(
        replace_summary_block(summary, summary_block(period, metrics, policy["ledger_path"], report_path_text)),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Brand64 observation date (YYYY-MM-DD)")
    parser.add_argument("--input", type=Path, help="Verified official-page candidate JSON/JSONL")
    parser.add_argument("--apply", action="store_true", help="Write the ledger, report, daily metrics, and summary")
    parser.add_argument("--strict", action="store_true", help="Fail instead of cleanly skipping when the readiness gate is closed")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = execute(args.root, run_date=args.date, input_path=args.input, apply=args.apply, strict=args.strict)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
