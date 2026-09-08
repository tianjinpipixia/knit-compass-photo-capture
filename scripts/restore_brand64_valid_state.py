#!/usr/bin/env python3
"""Restore Brand64 state from the newest strict-valid durable baseline.

Never accepts a corrupt or suspiciously empty known-products.json. Candidates are
checked in order: flash-feed, recent Actions artifacts, recent direct result branches.
The first strict UTF-8 JSON object with a substantial product baseline is restored.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path("data/brand-md-monitoring/direct-scans")
STATE_FILES = [
    "known-products.json",
    "coverage-state.json",
    "deep-dive-queue.json",
    "flash-history.json",
    "detail-results.json",
]
MIN_KNOWN_PRODUCTS = 500


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def strict_json(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    return json.loads(text)


def validate_candidate(directory: Path, label: str) -> bool:
    known_path = directory / "known-products.json"
    if not known_path.is_file():
        print(f"REJECT {label}: known-products.json missing")
        return False
    try:
        known = strict_json(known_path)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"REJECT {label}: invalid UTF-8/JSON: {exc}")
        return False
    if not isinstance(known, dict):
        print(f"REJECT {label}: known-products is not an object")
        return False
    if len(known) < MIN_KNOWN_PRODUCTS:
        print(f"REJECT {label}: only {len(known)} known products (< {MIN_KNOWN_PRODUCTS})")
        return False
    for name in STATE_FILES[1:]:
        path = directory / name
        if not path.exists():
            continue
        try:
            value = strict_json(path)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"REJECT {label}: {name} invalid: {exc}")
            return False
        if not isinstance(value, (dict, list)):
            print(f"REJECT {label}: {name} has unexpected root type")
            return False
    print(f"ACCEPT {label}: {len(known)} strict-valid known products")
    return True


def copy_state(source: Path, label: str) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for name in STATE_FILES:
        src = source / name
        if src.is_file():
            shutil.copy2(src, ROOT / name)
        else:
            (ROOT / name).unlink(missing_ok=True)
    print(f"RESTORED_SOURCE={label}")


def extract_ref(ref: str, directory: Path) -> bool:
    directory.mkdir(parents=True, exist_ok=True)
    run("git", "fetch", "--depth=1", "origin", ref)
    found = False
    for name in STATE_FILES:
        probe = run(
            "git", "cat-file", "-e",
            f"FETCH_HEAD:data/brand-md-monitoring/direct-scans/{name}",
            check=False,
        )
        if probe.returncode != 0:
            continue
        content = run(
            "git", "show",
            f"FETCH_HEAD:data/brand-md-monitoring/direct-scans/{name}",
        ).stdout
        (directory / name).write_bytes(content.encode("utf-8", errors="strict"))
        found = True
    return found


def try_flash(tmp: Path) -> bool:
    ref = run("git", "ls-remote", "--heads", "origin", "refs/heads/brand64/flash-feed").stdout.strip()
    if not ref:
        return False
    directory = tmp / "flash-feed"
    try:
        if extract_ref("brand64/flash-feed", directory) and validate_candidate(directory, "brand64/flash-feed"):
            copy_state(directory, "brand64/flash-feed")
            return True
    except (subprocess.CalledProcessError, UnicodeEncodeError) as exc:
        print(f"REJECT brand64/flash-feed: extraction failed: {exc}")
    return False


def try_artifacts(tmp: Path) -> bool:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo or not shutil.which("gh"):
        return False
    runs = run(
        "gh", "api", "--method", "GET",
        f"repos/{repo}/actions/workflows/run-brand64-gemini-primary-scan.yml/runs",
        "-f", "status=completed", "-f", "branch=main", "-f", "per_page=30",
        "--jq", ".workflow_runs[].id",
        check=False,
    )
    if runs.returncode != 0:
        return False
    for run_id in [line.strip() for line in runs.stdout.splitlines() if line.strip()]:
        artifacts = run(
            "gh", "api", f"repos/{repo}/actions/runs/{run_id}/artifacts",
            "--jq", '[.artifacts[] | select(.expired == false) | select(.name | startswith("brand64-free-direct-"))] | sort_by(.created_at, .id) | reverse | .[].name',
            check=False,
        )
        if artifacts.returncode != 0:
            continue
        for artifact_name in [line.strip() for line in artifacts.stdout.splitlines() if line.strip()]:
            directory = tmp / f"artifact-{run_id}-{artifact_name.replace('/', '_')}"
            directory.mkdir(parents=True, exist_ok=True)
            download = run("gh", "run", "download", run_id, "--name", artifact_name, "--dir", str(directory), check=False)
            if download.returncode != 0:
                continue
            candidates = [directory, *[p.parent for p in directory.rglob("known-products.json")]]
            for candidate in candidates:
                if validate_candidate(candidate, f"artifact:{run_id}:{artifact_name}"):
                    copy_state(candidate, f"artifact:{run_id}:{artifact_name}")
                    return True
    return False


def try_direct_branches(tmp: Path) -> bool:
    refs = run("git", "ls-remote", "--heads", "origin", "refs/heads/brand64/direct-*").stdout.splitlines()
    branch_names = [line.split()[1].removeprefix("refs/heads/") for line in refs if line.strip()]
    branch_names.sort(reverse=True)
    for branch in branch_names[:40]:
        directory = tmp / branch.replace("/", "_")
        try:
            if not extract_ref(branch, directory):
                continue
            if validate_candidate(directory, branch):
                copy_state(directory, branch)
                return True
        except (subprocess.CalledProcessError, UnicodeEncodeError) as exc:
            print(f"REJECT {branch}: extraction failed: {exc}")
    return False


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        tmp = Path(work)
        if try_flash(tmp) or try_artifacts(tmp) or try_direct_branches(tmp):
            # Final strict check on exactly what downstream code will read.
            if not validate_candidate(ROOT, "restored-working-state"):
                raise SystemExit("Restored state failed final validation")
            return 0
    raise SystemExit("Previous Brand64 observations exist, but no strict-valid baseline could be restored. Refusing to reset history.")


if __name__ == "__main__":
    raise SystemExit(main())
