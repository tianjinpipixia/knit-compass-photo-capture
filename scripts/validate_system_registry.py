#!/usr/bin/env python3
"""Validate the Knit Compass connection registry, source revisions, and KPI schema."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

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
HEX_SHA256 = re.compile(r"[0-9a-f]{64}")


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


def git_command_bytes(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=False,
    )


def directory_content_sha256(source: str) -> str:
    dirty = git_command_bytes(
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        source,
    )
    if dirty.returncode != 0:
        fail(
            f"could not inspect working-tree state under {source}: "
            f"{dirty.stderr.decode(errors='replace').strip() or 'git status failed'}"
        )
    if dirty.stdout:
        changed_paths = []
        for record in dirty.stdout.split(b"\0"):
            if not record:
                continue
            changed_paths.append(os.fsdecode(record[3:] if len(record) > 3 else record))
        fail(
            f"registered directory {source} has staged, unstaged, deleted, mode-changed, "
            f"or untracked files; commit or restore them before validation: {changed_paths}"
        )

    listed = git_command_bytes("ls-files", "--stage", "-z", "--", source)
    if listed.returncode != 0:
        fail(
            f"could not list tracked files under {source}: "
            f"{listed.stderr.decode(errors='replace').strip() or 'git ls-files failed'}"
        )

    entries: list[tuple[bytes, bytes, bytes]] = []
    for record in listed.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, path_bytes = record.partition(b"\t")
        if not separator:
            fail(
                f"unexpected NUL-delimited git ls-files output for {source}: "
                f"{record!r}"
            )
        parts = metadata.split()
        if len(parts) != 3:
            fail(
                f"unexpected git index metadata for {os.fsdecode(path_bytes)}: "
                f"{metadata!r}"
            )
        mode, blob_sha, stage = parts
        if stage != b"0":
            fail(f"unmerged git index entry under {source}: {os.fsdecode(path_bytes)}")
        if not HEX_SHA.fullmatch(blob_sha.decode("ascii", errors="strict")):
            fail(f"invalid git blob SHA under {source}: {blob_sha!r}")

        working_path = ROOT / os.fsdecode(path_bytes)
        if not working_path.is_file():
            fail(f"tracked working-tree file is missing under {source}: {working_path}")
        working_blob_sha = git_blob_sha(working_path).encode("ascii")
        if working_blob_sha != blob_sha:
            fail(
                f"working-tree content differs from the index under {source}: "
                f"{os.fsdecode(path_bytes)}"
            )
        entries.append((path_bytes, mode, working_blob_sha))

    if not entries:
        fail(f"directory source has no tracked files: {source}")

    digest_input = b"".join(
        mode + b" " + path_bytes + b"\0" + blob_sha + b"\n"
        for path_bytes, mode, blob_sha in sorted(entries, key=lambda item: item[0])
    )
    return hashlib.sha256(digest_input).hexdigest()


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

    if revision.startswith("content-sha256:"):
        if candidate is None or not candidate.is_dir():
            fail(f"{system_id} content-sha256 revision requires a directory code_source")
        expected = revision.removeprefix("content-sha256:")
        if not HEX_SHA256.fullmatch(expected):
            fail(f"{system_id} has invalid content SHA-256: {expected}")
        source = source_name(code_source)
        actual = directory_content_sha256(source)
        if actual != expected:
            fail(
                f"{system_id} directory revision mismatch for {source}: "
                f"expected {expected}, actual {actual}"
            )
        return

    fail(
        f"{system_id} uses unsupported code_revision format: {revision}; "
        "use git-blob for files or content-sha256 for directories"
    )


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
    if not android["code_revision"].startswith("content-sha256:"):
        fail("KC-DAILY-ANDROID must use a squash-safe content-sha256 revision")

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


def registered_source_patterns(systems: list[dict[str, Any]]) -> set[str]:
    sources: set[str] = set()
    for system in systems:
        sources.add(source_name(system["code_source"]))
        for auxiliary in system.get("auxiliary_sources", []):
            sources.add(source_name(auxiliary["code_source"]))

    patterns: set[str] = set()
    for source in sources:
        if source in {"repository-root", "apk"}:
            continue
        path = ROOT / source
        patterns.add(f"{source}/**" if path.is_dir() else source)
    return patterns


def event_paths(workflow: dict[str, Any], event_name: str) -> list[str]:
    triggers = workflow.get("on")
    if not isinstance(triggers, dict):
        fail('workflow must contain a mapping under quoted key "on"')
    event = triggers.get(event_name)
    if not isinstance(event, dict):
        fail(f"workflow trigger {event_name} must be a mapping")
    paths = event.get("paths")
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        fail(f"workflow trigger {event_name}.paths must be a string array")
    return paths


def validate_workflow_paths(systems: list[dict[str, Any]]) -> None:
    try:
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing {WORKFLOW_PATH.relative_to(ROOT)}")
    except yaml.YAMLError as error:
        fail(f"invalid workflow YAML: {error}")

    if not isinstance(workflow, dict):
        fail("workflow root must be a mapping")

    required_patterns = registered_source_patterns(systems)
    for event_name in ("pull_request", "push"):
        paths = event_paths(workflow, event_name)
        negative_patterns = [pattern for pattern in paths if pattern.startswith("!")]
        if negative_patterns:
            fail(
                f"workflow {event_name}.paths may not contain exclusions because they "
                f"can negate registered sources: {negative_patterns}"
            )
        missing = required_patterns - set(paths)
        if missing:
            fail(
                f"workflow {event_name}.paths missing registered sources: "
                f"{sorted(missing)}"
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
        "PASS: registry fields, clean squash-safe source revisions, ordered trigger paths, "
        "browser storage declarations, status display, KPI schema, and start scripts"
    )


if __name__ == "__main__":
    main()
