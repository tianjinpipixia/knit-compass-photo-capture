#!/usr/bin/env python3
"""Validate the Knit Compass connection registry, source revisions, and KPI schema."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "system-registry.json"
STATUS_PAGE_PATH = ROOT / "status" / "index.html"
KPI_TEMPLATE_PATH = ROOT / "data" / "kpi_log_template.csv"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "validate-system-registry.yml"

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
HEX_SHA = re.compile(r"[0-9a-f]{40}")


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


def source_name(code_source: str) -> str:
    return code_source.split("@", 1)[0]


def source_path(code_source: str) -> Path | None:
    source = source_name(code_source)
    if source in {"repository-root", "apk"}:
        return None
    return ROOT / source


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def git_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def validate_source_revision(system_id: str, code_source: str, revision: str) -> None:
    candidate = source_path(code_source)
    if candidate is not None and not candidate.exists():
        fail(
            f"{system_id} code_source points to missing path: "
            f"{candidate.relative_to(ROOT)}"
        )

    if revision.startswith("git-blob:"):
        if candidate is None or not candidate.is_file():
            fail(f"{system_id} git-blob revision requires a file code_source")
        expected = revision.removeprefix("git-blob:")
        if not HEX_SHA.fullmatch(expected):
            fail(f"{system_id} has invalid git-blob SHA: {expected}")
        actual = git_blob_sha(candidate)
        if actual != expected:
            fail(
                f"{system_id} code_revision mismatch for "
                f"{candidate.relative_to(ROOT)}: expected {expected}, actual {actual}"
            )
        return

    if revision.startswith("git-commit:"):
        expected = revision.removeprefix("git-commit:")
        if not HEX_SHA.fullmatch(expected):
            fail(f"{system_id} has invalid git-commit SHA: {expected}")
        if git_command("cat-file", "-e", f"{expected}^{{commit}}").returncode != 0:
            fail(f"{system_id} git commit is unavailable: {expected}")
        if git_command("merge-base", "--is-ancestor", expected, "HEAD").returncode != 0:
            fail(f"{system_id} git commit is not reachable from HEAD: {expected}")
        source = source_name(code_source)
        if source not in {"repository-root", "apk"}:
            if git_command("cat-file", "-e", f"{expected}:{source}").returncode != 0:
                fail(f"{system_id} source {source} is absent at commit {expected}")
        return

    fail(f"{system_id} uses unsupported code_revision format: {revision}")


def validate_registry(registry: dict[str, Any]) -> list[dict[str, Any]]:
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

        validate_source_revision(
            system_id,
            system["code_source"],
            system["code_revision"],
        )

        auxiliary_sources = system.get("auxiliary_sources", [])
        if not isinstance(auxiliary_sources, list):
            fail(f"{system_id} auxiliary_sources must be an array")
        for auxiliary in auxiliary_sources:
            if not isinstance(auxiliary, dict):
                fail(f"{system_id} auxiliary source must be an object")
            if not auxiliary.get("code_source") or not auxiliary.get("code_revision"):
                fail(f"{system_id} auxiliary source is missing code_source/code_revision")
            validate_source_revision(
                f"{system_id} auxiliary",
                auxiliary["code_source"],
                auxiliary["code_revision"],
            )

    android = next(
        (system for system in systems if system["system_id"] == "KC-DAILY-ANDROID"),
        None,
    )
    if android is None:
        fail("KC-DAILY-ANDROID is missing")
    if not android["code_source"].startswith("android-daily"):
        fail("KC-DAILY-ANDROID code_source must point to android-daily")

    return systems


def validate_photo_capture_storage(systems: list[dict[str, Any]]) -> None:
    photo_capture = next(
        (system for system in systems if system["system_id"] == "KC-PHOTO-CAPTURE"),
        None,
    )
    if photo_capture is None:
        fail("KC-PHOTO-CAPTURE is missing")

    app_text = (ROOT / "app.js").read_text(encoding="utf-8")
    backup_text = (ROOT / "backup.js").read_text(encoding="utf-8")
    app_match = re.search(r"const DB='([^']+)',SESSION='([^']+)'", app_text)
    backup_match = re.search(r"const LAST_BACKUP_KEY = '([^']+)'", backup_text)
    if app_match is None or backup_match is None:
        fail("could not extract Photo Capture browser storage keys")

    storage_detail = str(photo_capture.get("storage_detail") or "")
    for key in (*app_match.groups(), backup_match.group(1)):
        if key not in storage_detail:
            fail(f"Photo Capture storage_detail does not declare {key}")

    auxiliary_sources = photo_capture.get("auxiliary_sources") or []
    if not any(source.get("code_source") == "backup.js@main" for source in auxiliary_sources):
        fail("Photo Capture must register backup.js as an auxiliary source")


def validate_workflow_paths(systems: list[dict[str, Any]]) -> None:
    try:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing {WORKFLOW_PATH.relative_to(ROOT)}")

    sources: set[str] = set()
    for system in systems:
        sources.add(source_name(system["code_source"]))
        for auxiliary in system.get("auxiliary_sources", []):
            sources.add(source_name(auxiliary["code_source"]))

    for source in sources:
        if source in {"repository-root", "apk"}:
            continue
        path = ROOT / source
        pattern = f"{source}/**" if path.is_dir() else source
        if workflow.count(f'"{pattern}"') < 2:
            fail(
                f"workflow paths must include {pattern} for both pull_request and push"
            )


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
    systems = validate_registry(registry)
    validate_photo_capture_storage(systems)
    validate_workflow_paths(systems)
    validate_status_page()
    validate_kpi_template()
    validate_start_scripts()
    print(
        "PASS: registry fields, exact source revisions, workflow paths, "
        "browser storage declarations, status display, KPI schema, and start scripts"
    )


if __name__ == "__main__":
    main()
