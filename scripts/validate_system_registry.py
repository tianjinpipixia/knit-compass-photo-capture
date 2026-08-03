#!/usr/bin/env python3
"""Validate the static Knit Compass connection registry and KPI ledger schema."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "system-registry.json"
STATUS_PAGE_PATH = ROOT / "status" / "index.html"
KPI_TEMPLATE_PATH = ROOT / "data" / "kpi_log_template.csv"

REQUIRED_SYSTEM_FIELDS = {
    "environment",
    "system_id",
    "display_name",
    "display_version",
    "code_revision",
    "code_source",
    "entry_path",
    "data_store",
    "sync_mode",
    "last_sync_at",
    "external_database",
    "status",
}
REQUIRED_KPI_COLUMNS = {
    "measurement_date",
    "operator",
    "workflow",
    "event_type",
    "item_type",
    "item_id",
    "registration_status",
    "confirmed_at",
    "baseline_minutes",
    "actual_minutes",
    "minutes_saved",
    "ai_tool",
    "ai_correction_count",
    "human_review_status",
    "evidence_id",
    "evidence_status",
    "reuse_count",
    "active_user_count",
    "notes",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load_registry() -> dict[str, Any]:
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing {REGISTRY_PATH.relative_to(ROOT)}")
    except json.JSONDecodeError as error:
        fail(f"invalid JSON in {REGISTRY_PATH.relative_to(ROOT)}: {error}")
    if not isinstance(data, dict):
        fail("registry root must be an object")
    return data


def source_path(code_source: str) -> Path | None:
    source = code_source.split("@", 1)[0]
    if source in {"repository-root", "apk"}:
        return None
    return ROOT / source


def validate_registry(registry: dict[str, Any]) -> None:
    policy = registry.get("policy")
    if not isinstance(policy, dict):
        fail("policy must be an object")

    declared_ui_fields = set(policy.get("required_ui_fields") or [])
    missing_policy_fields = {
        "environment",
        "system_id",
        "display_version",
        "code_revision",
        "data_store",
        "sync_mode",
        "last_sync_at",
    } - declared_ui_fields
    if missing_policy_fields:
        fail(f"policy.required_ui_fields missing: {sorted(missing_policy_fields)}")

    systems = registry.get("systems")
    if not isinstance(systems, list) or not systems:
        fail("systems must be a non-empty array")

    seen_ids: set[str] = set()
    for index, system in enumerate(systems):
        if not isinstance(system, dict):
            fail(f"systems[{index}] must be an object")

        missing = REQUIRED_SYSTEM_FIELDS - set(system)
        if missing:
            fail(f"{system.get('system_id', index)} missing fields: {sorted(missing)}")

        empty = [
            field
            for field in REQUIRED_SYSTEM_FIELDS
            if not isinstance(system.get(field), str) or not system[field].strip()
        ]
        if empty:
            fail(f"{system.get('system_id', index)} has empty fields: {sorted(empty)}")

        system_id = system["system_id"]
        if system_id in seen_ids:
            fail(f"duplicate system_id: {system_id}")
        seen_ids.add(system_id)

        candidate = source_path(system["code_source"])
        if candidate is not None and not candidate.exists():
            fail(
                f"{system_id} code_source points to missing path: "
                f"{candidate.relative_to(ROOT)}"
            )

    android = next(
        (system for system in systems if system["system_id"] == "KC-DAILY-ANDROID"),
        None,
    )
    if android is None:
        fail("KC-DAILY-ANDROID is missing")
    if not android["code_source"].startswith("android-daily"):
        fail("KC-DAILY-ANDROID code_source must point to android-daily")


def validate_status_page() -> None:
    try:
        html = STATUS_PAGE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing {STATUS_PAGE_PATH.relative_to(ROOT)}")

    for field in (
        "environment",
        "display_version",
        "code_revision",
        "data_store",
        "sync_mode",
        "last_sync_at",
        "external_database",
    ):
        if f"system.{field}" not in html:
            fail(f"status page does not render {field}")


def validate_kpi_template() -> None:
    try:
        with KPI_TEMPLATE_PATH.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)
    except FileNotFoundError:
        fail(f"missing {KPI_TEMPLATE_PATH.relative_to(ROOT)}")
    except StopIteration:
        fail("KPI template is empty")

    missing = REQUIRED_KPI_COLUMNS - set(header)
    if missing:
        fail(f"KPI template missing columns: {sorted(missing)}")
    if len(header) != len(set(header)):
        fail("KPI template contains duplicate columns")


def validate_start_scripts() -> None:
    for relative_path in ("start.bat", "start.sh"):
        path = ROOT / relative_path
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            fail(f"missing or empty {relative_path}")


def main() -> None:
    registry = load_registry()
    validate_registry(registry)
    validate_status_page()
    validate_kpi_template()
    validate_start_scripts()
    print(
        "PASS: system registry, status display, KPI schema, "
        "Android source path, and local start scripts"
    )


if __name__ == "__main__":
    main()
