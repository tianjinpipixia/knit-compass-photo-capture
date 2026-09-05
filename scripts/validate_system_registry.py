#!/usr/bin/env python3
"""Validate Knit Compass registry, source revisions, UI disclosure, and KPI schema."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/system-registry.json"
STATUS = ROOT / "status/index.html"
WORKFLOW = ROOT / ".github/workflows/validate-system-registry.yml"
KPI = ROOT / "data/kpi_log_template.csv"
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
REQUIRED = {
    "environment", "system_id", "display_name", "display_version", "code_revision",
    "code_source", "entry_path", "entry_href", "entry_label", "data_store", "sync_mode", "last_sync_at",
    "external_database", "status",
}
KPI_COLUMNS = {
    "measurement_date", "operator", "workflow", "event_type", "item_type", "item_id",
    "registration_status", "confirmed_at", "baseline_minutes", "actual_minutes",
    "minutes_saved", "ai_tool", "ai_correction_count", "human_review_status",
    "evidence_id", "evidence_status", "reuse_count", "active_user_count", "notes",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def git(*args: str, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, check=False, capture_output=True, text=not binary)


def source_name(value: str) -> str:
    return value.split("@", 1)[0]


def source_path(value: str) -> Path | None:
    name = source_name(value)
    return None if name in {"repository-root", "apk"} else ROOT / name


def worktree_blob(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    result = git("hash-object", f"--path={relative}", "--", relative)
    if result.returncode:
        fail(f"git hash-object failed for {relative}: {result.stderr.strip()}")
    digest = result.stdout.strip()
    if not HEX40.fullmatch(digest):
        fail(f"invalid blob SHA for {relative}: {digest}")
    return digest


def directory_digest(name: str) -> str:
    dirty = git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--", name, binary=True)
    if dirty.returncode:
        fail(f"git status failed for {name}")
    if dirty.stdout:
        fail(f"registered directory has uncommitted changes: {name}")
    listed = git("ls-files", "--stage", "-z", "--", name, binary=True)
    if listed.returncode:
        fail(f"git ls-files failed for {name}")
    entries: list[tuple[bytes, bytes, bytes]] = []
    for record in listed.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, path_bytes = record.partition(b"\t")
        if not separator:
            fail(f"unexpected index record under {name}")
        mode, blob_sha, stage = metadata.split()
        if stage != b"0" or mode not in {b"100644", b"100755"}:
            fail(f"unsupported index entry: {os.fsdecode(path_bytes)}")
        path = ROOT / os.fsdecode(path_bytes)
        if not path.is_file():
            fail(f"missing tracked file: {path.relative_to(ROOT)}")
        if os.name != "nt":
            actual_mode = b"100755" if path.stat().st_mode & stat.S_IXUSR else b"100644"
            if actual_mode != mode:
                fail(f"mode mismatch: {path.relative_to(ROOT)}")
        actual_blob = worktree_blob(path).encode()
        if actual_blob != blob_sha:
            fail(f"content differs from index: {path.relative_to(ROOT)}")
        entries.append((path_bytes, mode, actual_blob))
    if not entries:
        fail(f"directory has no tracked files: {name}")
    payload = b"".join(mode + b" " + path + b"\0" + sha + b"\n" for path, mode, sha in sorted(entries))
    return hashlib.sha256(payload).hexdigest()


def validate_revision(system_id: str, source: str, revision: str) -> None:
    path = source_path(source)
    if path is not None and not path.exists():
        fail(f"{system_id} source missing: {path.relative_to(ROOT)}")
    if revision.startswith("git-blob:"):
        expected = revision.removeprefix("git-blob:")
        if path is None or not path.is_file() or not HEX40.fullmatch(expected):
            fail(f"{system_id} invalid git-blob registration")
        actual = worktree_blob(path)
        if actual != expected:
            fail(f"{system_id} revision mismatch: expected {expected}, actual {actual}")
        return
    if revision.startswith("content-sha256:"):
        expected = revision.removeprefix("content-sha256:")
        if path is None or not path.is_dir() or not HEX64.fullmatch(expected):
            fail(f"{system_id} invalid content-sha256 registration")
        actual = directory_digest(source_name(source))
        if actual != expected:
            fail(f"{system_id} directory revision mismatch: expected {expected}, actual {actual}")
        return
    fail(f"{system_id} unsupported revision format: {revision}")


def validate_entry_link(system: dict[str, Any]) -> None:
    value = system["entry_href"]
    parsed = urlsplit(value)
    if parsed.scheme:
        if parsed.scheme != "https" or not parsed.netloc:
            fail(f"{system['system_id']} entry_href must be a valid HTTPS URL")
        return
    if parsed.netloc or not parsed.path:
        fail(f"{system['system_id']} entry_href is invalid")
    target = (STATUS.parent / unquote(parsed.path)).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        fail(f"{system['system_id']} entry_href leaves the repository")
    if target.is_dir() or parsed.path.endswith("/"):
        target /= "index.html"
    if not target.is_file():
        fail(f"{system['system_id']} entry_href target missing: {target}")


def load_registry() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read registry: {error}")
    systems = registry.get("systems")
    if not isinstance(systems, list) or not systems:
        fail("systems must be a non-empty array")
    ui_fields = set(registry.get("policy", {}).get("required_ui_fields") or [])
    if {"environment", "system_id", "display_version", "code_revision", "data_store", "sync_mode", "last_sync_at"} - ui_fields:
        fail("policy.required_ui_fields is incomplete")
    seen: set[str] = set()
    for system in systems:
        if not isinstance(system, dict):
            fail("system entry must be an object")
        missing = REQUIRED - set(system)
        if missing:
            fail(f"{system.get('system_id', '?')} missing fields: {sorted(missing)}")
        if any(not isinstance(system.get(key), str) or not system[key].strip() for key in REQUIRED):
            fail(f"{system.get('system_id', '?')} contains empty required values")
        if system["system_id"] in seen:
            fail(f"duplicate system_id: {system['system_id']}")
        seen.add(system["system_id"])
        validate_entry_link(system)
        validate_revision(system["system_id"], system["code_source"], system["code_revision"])
        auxiliaries = system.get("auxiliary_sources", [])
        if not isinstance(auxiliaries, list):
            fail(f"{system['system_id']} auxiliary_sources must be an array")
        for auxiliary in auxiliaries:
            validate_revision(f"{system['system_id']} auxiliary", auxiliary.get("code_source", ""), auxiliary.get("code_revision", ""))
    android = next((row for row in systems if row["system_id"] == "KC-DAILY-ANDROID"), None)
    if not android or not android["code_source"].startswith("android-daily") or not android["code_revision"].startswith("content-sha256:"):
        fail("KC-DAILY-ANDROID must use android-daily content-sha256")
    return registry, systems


def validate_photo_storage(systems: list[dict[str, Any]]) -> None:
    photo = next((row for row in systems if row["system_id"] == "KC-PHOTO-CAPTURE"), None)
    if not photo:
        fail("KC-PHOTO-CAPTURE missing")
    app_text = (ROOT / "app.js").read_text(encoding="utf-8")
    backup_text = (ROOT / "backup.js").read_text(encoding="utf-8")
    # The independent runtime declares its database in CONTRACT and transfers
    # records through portable ZIPs. Legacy HANDOFF_KEY is owned by the receiver.
    patterns = [
        r"""\bdatabase_name\s*:\s*["']([^"']+)["']""",
        r"""\bconst\s+SESSION_KEY\s*=\s*["']([^"']+)["']""",
    ]
    keys = []
    for pattern in patterns:
        match = re.search(pattern, app_text)
        if not match:
            fail(f"could not extract Photo Capture storage key: {pattern}")
        keys.append(match.group(1))
    for constant in ("LAST_BACKUP_KEY", "LAST_VERIFIED_BACKUP_KEY", "LAST_DATA_CHANGE_KEY"):
        backup = re.search(rf"""\bconst\s+{constant}\s*=\s*["']([^"']+)["']""", backup_text)
        if not backup:
            fail(f"could not extract backup timestamp key: {constant}")
        keys.append(backup.group(1))
    backup_db = re.search(r"""\bconst\s+DB_NAME\s*=\s*["']([^"']+)["']""", backup_text)
    if not backup_db or backup_db.group(1) != keys[0]:
        fail("Photo Capture and backup database names must agree")
    detail = str(photo.get("storage_detail") or "")
    for key in keys:
        if key not in detail:
            fail(f"Photo Capture storage_detail missing {key}")
    if not any(row.get("code_source") == "backup.js@main" for row in photo.get("auxiliary_sources", [])):
        fail("Photo Capture must register backup.js")
    if not any(row.get("code_source") == "sw.js@main" for row in photo.get("auxiliary_sources", [])):
        fail("Photo Capture must register its install service worker")


def validate_workflow(systems: list[dict[str, Any]]) -> None:
    try:
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        fail(f"cannot read workflow: {error}")
    required = {".gitattributes", "**/.gitattributes"}
    for system in systems:
        sources = [system["code_source"], *[row["code_source"] for row in system.get("auxiliary_sources", [])]]
        for source in sources:
            name = source_name(source)
            if name in {"repository-root", "apk"}:
                continue
            required.add(f"{name}/**" if (ROOT / name).is_dir() else name)
    triggers = workflow.get("on") if isinstance(workflow, dict) else None
    if not isinstance(triggers, dict):
        fail('workflow must use quoted mapping key "on"')
    for event_name in ("pull_request", "push"):
        paths = triggers.get(event_name, {}).get("paths")
        if not isinstance(paths, list):
            fail(f"workflow {event_name}.paths missing")
        if any(str(value).startswith("!") for value in paths):
            fail(f"workflow {event_name}.paths may not use exclusions")
        missing = required - set(paths)
        if missing:
            fail(f"workflow {event_name}.paths missing: {sorted(missing)}")


def validate_status_page(registry: dict[str, Any], systems: list[dict[str, Any]]) -> None:
    html = STATUS.read_text(encoding="utf-8")
    for label in ("環境", "表示バージョン", "コードRevision", "保存先", "同期", "最終同期", "外部DB"):
        if label not in html:
            fail(f"status page missing label: {label}")
    for system in systems:
        if system["system_id"] not in json.dumps(registry, ensure_ascii=False):
            fail(f"registry lost system id: {system['system_id']}")
    for token in ('system.entry_href', 'system.entry_label', 'class="launch"'):
        if token not in html:
            fail(f"status page is not rendering registered entry links: {token}")


def validate_kpi() -> None:
    with KPI.open(encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle), [])
    missing = KPI_COLUMNS - set(header)
    if missing:
        fail(f"KPI template missing columns: {sorted(missing)}")
    if len(header) != len(set(header)):
        fail("KPI template contains duplicate columns")


def main() -> None:
    registry, systems = load_registry()
    validate_photo_storage(systems)
    validate_workflow(systems)
    validate_status_page(registry, systems)
    validate_kpi()
    print(f"OK: validated {len(systems)} systems, revisions, handoff storage, workflow paths, status UI, and KPI schema")


if __name__ == "__main__":
    main()
