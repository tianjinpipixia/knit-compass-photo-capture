#!/usr/bin/env python3
"""Publish bounded MD baseline references *after* canonical daily binding.

Only writes an additive index on the existing brand64/flash-feed branch.
No product snapshots are rewritten, no new crawl and no AI API calls.
The index records bound commits, NOT independently completed Actions runs.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DIRECT = ROOT / "data/brand-md-monitoring/direct-scans"
BRANCH = "brand64/flash-feed"
PREFIX = "data/brand-md-monitoring/direct-scans/"
INDEX = "md-baseline-index.json"
FORMAT = "KC_BRAND64_MD_BASELINE_INDEX"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def valid_day(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", value):
        raise ValueError("MD_BASELINE_DATE_INVALID")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("MD_BASELINE_DATE_INVALID") from error


def check_record(item: dict) -> None:
    if not isinstance(item, dict) or not HEX40.fullmatch(str(item.get("bound_commit", ""))) or (
        not HEX64.fullmatch(str(item.get("canonical_manifest_sha256", "")))
    ) or not str(item.get("collection_run_id", "")).isdigit():
        raise ValueError("MD_BASELINE_RECORD_INVALID")
    valid_day(item.get("observation_date", ""))


def build_index(prior: dict | None, bound_commit: str, binding: dict) -> dict:
    if not HEX40.fullmatch(bound_commit):
        raise ValueError("MD_BASELINE_SOURCE_COMMIT_INVALID")
    if not isinstance(binding, dict) or binding.get("format") != "KC_BRAND64_DAILY_PIPELINE_SNAPSHOT":
        raise ValueError("MD_BASELINE_BINDING_INVALID")
    if binding.get("canonical_status") != "VALIDATED" or binding.get("analysis_ready") is not True:
        raise ValueError("MD_BASELINE_NOT_VALIDATED")
    if binding.get("publication_status") != "PUBLISH_HOLD" or binding.get("human_review_required") is not True or binding.get("formal_product_registration") is not False:
        raise ValueError("MD_BASELINE_PUBLICATION_BOUNDARY")
    record = {
        "observation_date": str(binding["observation_date"]),
        "bound_commit": bound_commit,
        "collection_run_id": str(binding["collection_run_id"]),
        "canonical_manifest_sha256": str(binding["canonical_manifest_sha256"]),
    }
    check_record(record)
    present = []
    if prior is not None:
        if not isinstance(prior, dict) or prior.get("format") != FORMAT or prior.get("branch") != BRANCH or not isinstance(prior.get("entries"), list):
            raise ValueError("MD_BASELINE_INDEX_FORMAT_INVALID")
        present = prior["entries"]
        for item in present:
            check_record(item)
    current_date = valid_day(record["observation_date"])
    dates_seen = set()
    kept = []
    for item in [record, *present]:
        observed = valid_day(item["observation_date"])
        age = (current_date - observed).days
        if not 0 <= age <= 6 or item["observation_date"] in dates_seen:
            continue
        kept.append(dict(item))
        dates_seen.add(item["observation_date"])
    kept.sort(key=lambda item: item["observation_date"], reverse=True)
    return {
        "format": FORMAT, "schema_version": "1.0",
        "branch": BRANCH, "anchor_observation_date": record["observation_date"],
        "index_is_run_success_proof": False,
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True, "formal_product_registration": False,
        "entries": kept[:7],
    }


def git(*args: str, input_bytes: bytes | None = None, env: dict | None = None, check=True):
    return subprocess.run(
        ["git", *args], input=input_bytes, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=env, check=check
    )


def publish_index(binding: dict, *, expected_run_id: str) -> dict:
    if not expected_run_id or binding.get("collection_run_id") != expected_run_id:
        raise ValueError("MD_BASELINE_RUN_ID_MISMATCH")
    git("fetch", "--depth=1", "origin", BRANCH)
    parent = git("rev-parse", "FETCH_HEAD").stdout.decode().strip()
    # The prior publishing step must have just committed this exact binding.
    from_remote = git("show", f"{parent}:{PREFIX}snapshot-binding.json").stdout
    if json.loads(from_remote) != binding:
        raise ValueError("MD_BASELINE_REMOTE_BINDING_MISMATCH")
    path = f"{PREFIX}{INDEX}"
    old = git("show", f"{parent}:{path}", check=False)
    if old.returncode == 0:
        prior = json.loads(old.stdout)
    elif b"does not exist" in old.stderr or b"exists on disk, but not in" in old.stderr:
        prior = None
    else:
        raise ValueError("MD_BASELINE_PRIOR_INDEX_UNREADABLE")
    result = build_index(prior, parent, binding)
    encoded = (json.dumps(result, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))+"\n").encode("utf-8")
    index_file = DIRECT / INDEX
    index_file.write_bytes(encoded)
    with tempfile.TemporaryDirectory() as folder:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(folder) / "index")}
        git("read-tree", parent, env=env)
        blob = git("hash-object", "-w", "--stdin", input_bytes=encoded).stdout.decode().strip()
        git("update-index", "--add", "--cacheinfo", "100644", blob, path, env=env)
        tree = git("write-tree", env=env).stdout.decode().strip()
        commit = git("commit-tree", tree, "-p", parent,
                     input_bytes=b"Index bound Brand64 MD source generations [skip ci]\n").stdout.decode().strip()
        git("push", "origin", f"{commit}:refs/heads/{BRANCH}")
    return {
        "index_commit": commit, "bound_source_commit": parent,
        "entry_count": len(result["entries"]),
        "anchor_date": result["anchor_observation_date"],
        "run_success_verified": False,
        "collector_extra_run_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-run-id", required=True)
    args = parser.parse_args()
    binding = json.loads((DIRECT / "snapshot-binding.json").read_text(encoding="utf-8"))
    result = publish_index(binding, expected_run_id=args.expected_run_id)
    print(json.dumps({"status": "MD_BASELINE_INDEX_UPDATED", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
