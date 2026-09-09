#!/usr/bin/env python3
"""Bind Brand64 official collection, canonical storage and Gemini MD analysis to one daily snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
DIRECT_ROOT = ROOT / "data/brand-md-monitoring/direct-scans"
GEMINI_ROOT = ROOT / "data/brand-md-monitoring/gemini-md"
BRANCH = "brand64/flash-feed"
PREFIX = "data/brand-md-monitoring/direct-scans/"
BINDING_NAME = "snapshot-binding.json"
MANIFEST_RELATIVE = "cumulative-products/manifest.json"
COLLECTOR = "CHATGPT_OFFICIAL_DIRECT"
ANALYZER = "GEMINI_PRIMARY"


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _required(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.is_file():
        raise ValueError(f"PIPELINE_SNAPSHOT_MISSING_FILE:{relative}")
    return path


def validate_canonical(root: Path, expected_date: str | None = None) -> Dict[str, Any]:
    latest_path = _required(root, "latest.json")
    feed_path = _required(root, "feed.json")
    coverage_path = _required(root, "coverage-state.json")
    manifest_path = _required(root, MANIFEST_RELATIVE)
    latest = read_json(latest_path)
    feed = read_json(feed_path)
    manifest = read_json(manifest_path)

    observation_date = str(latest.get("observed_date") or latest.get("observation_date") or "")
    if not observation_date or (expected_date and observation_date != expected_date):
        raise ValueError(f"PIPELINE_SNAPSHOT_DATE_MISMATCH:{observation_date}:{expected_date or ''}")
    if latest.get("collector") != COLLECTOR:
        raise ValueError(f"PIPELINE_COLLECTOR_MISMATCH:{latest.get('collector')}")
    if manifest.get("format") != "KC_BRAND64_CUMULATIVE_PRODUCTS_INDEX":
        raise ValueError("PIPELINE_CANONICAL_MANIFEST_INVALID")
    if manifest.get("observation_date") != observation_date:
        raise ValueError("PIPELINE_CANONICAL_DATE_MISMATCH")
    if (feed.get("summary") or {}).get("observed_date") != observation_date:
        raise ValueError("PIPELINE_FEED_DATE_MISMATCH")

    daily = manifest.get("daily_sources") or {}
    expected_latest_sha = ((daily.get("latest") or {}).get("sha256"))
    expected_feed_sha = ((daily.get("feed") or {}).get("sha256"))
    if not expected_latest_sha or expected_latest_sha != sha256_file(latest_path):
        raise ValueError("PIPELINE_LATEST_CHECKSUM_MISMATCH")
    if not expected_feed_sha or expected_feed_sha != sha256_file(feed_path):
        raise ValueError("PIPELINE_FEED_CHECKSUM_MISMATCH")

    seen = set()
    shard_count = 0
    for brand in manifest.get("brands") or []:
        brand_id = str(brand.get("brand_id") or "")
        relative = str(brand.get("path") or "")
        if not brand_id or brand_id in seen or relative != f"cumulative-products/{brand_id}.json":
            raise ValueError("PIPELINE_CANONICAL_BRAND_PATH_INVALID")
        seen.add(brand_id)
        shard_path = _required(root, relative)
        expected_sha = str(brand.get("sha256") or "")
        if not expected_sha or sha256_file(shard_path) != expected_sha:
            raise ValueError(f"PIPELINE_CANONICAL_SHARD_CHECKSUM_MISMATCH:{brand_id}")
        shard = read_json(shard_path)
        if shard.get("brand_id") != brand_id or shard.get("observation_date") != observation_date:
            raise ValueError(f"PIPELINE_CANONICAL_SHARD_GENERATION_MISMATCH:{brand_id}")
        records = shard.get("records") or []
        if len(records) != int(brand.get("product_count") or 0):
            raise ValueError(f"PIPELINE_CANONICAL_SHARD_COUNT_MISMATCH:{brand_id}")
        shard_count += len(records)
    if shard_count != int(manifest.get("cumulative_unique_product_count") or 0):
        raise ValueError("PIPELINE_CANONICAL_TOTAL_MISMATCH")

    return {
        "observation_date": observation_date,
        "latest": latest,
        "manifest": manifest,
        "hashes": {
            "latest": sha256_file(latest_path),
            "feed": sha256_file(feed_path),
            "coverage_state": sha256_file(coverage_path),
            "canonical_manifest": sha256_file(manifest_path),
        },
    }


def build_binding(root: Path, *, expected_date: str | None, collection_run_id: str,
                  collection_run_attempt: str = "", collector_source_sha: str = "") -> Dict[str, Any]:
    validated = validate_canonical(root, expected_date)
    latest = validated["latest"]
    manifest = validated["manifest"]
    binding = {
        "format": "KC_BRAND64_DAILY_PIPELINE_SNAPSHOT",
        "schema_version": "1.0",
        "observation_date": validated["observation_date"],
        "collector": COLLECTOR,
        "collection_method": str(latest.get("collection_method") or "DIRECT_HTTP_NO_AI_API"),
        "collection_run_id": str(collection_run_id),
        "collection_run_attempt": str(collection_run_attempt),
        "collector_source_sha": str(collector_source_sha),
        "canonical_status": "VALIDATED",
        "analysis_ready": True,
        "scan_status": str(latest.get("scan_status") or "UNKNOWN"),
        "canonical_manifest_path": MANIFEST_RELATIVE,
        "canonical_manifest_sha256": validated["hashes"]["canonical_manifest"],
        "canonical_unique_product_count": int(manifest.get("cumulative_unique_product_count") or 0),
        "observed_product_count_today": int(manifest.get("observed_product_count_today") or 0),
        "product_observed_brand_count_today": int(manifest.get("product_observed_brand_count_today") or 0),
        "snapshot_inputs": validated["hashes"],
        "publication_status": "PUBLISH_HOLD",
        "human_review_required": True,
        "formal_product_registration": False,
        "analysis_input_rule": "Gemini may analyze only this checksum-bound canonical generation; Gemini success is not a collection completion condition.",
    }
    write_json(root / BINDING_NAME, binding)
    return binding


def verify_binding(root: Path, *, expected_date: str | None = None,
                   expected_collection_run_id: str = "") -> Dict[str, Any]:
    binding_path = _required(root, BINDING_NAME)
    binding = read_json(binding_path)
    if binding.get("format") != "KC_BRAND64_DAILY_PIPELINE_SNAPSHOT":
        raise ValueError("PIPELINE_BINDING_FORMAT_INVALID")
    if binding.get("collector") != COLLECTOR:
        raise ValueError("PIPELINE_BINDING_COLLECTOR_INVALID")
    if binding.get("canonical_status") != "VALIDATED" or binding.get("analysis_ready") is not True:
        raise ValueError("PIPELINE_BINDING_NOT_ANALYSIS_READY")
    validated = validate_canonical(root, expected_date)
    if binding.get("observation_date") != validated["observation_date"]:
        raise ValueError("PIPELINE_BINDING_DATE_MISMATCH")
    if expected_collection_run_id and str(binding.get("collection_run_id") or "") != str(expected_collection_run_id):
        raise ValueError(
            f"PIPELINE_BINDING_RUN_MISMATCH:{binding.get('collection_run_id')}:{expected_collection_run_id}"
        )
    expected_hashes = binding.get("snapshot_inputs") or {}
    for key, actual in validated["hashes"].items():
        if str(expected_hashes.get(key) or "") != actual:
            raise ValueError(f"PIPELINE_BINDING_CHECKSUM_MISMATCH:{key}")
    if binding.get("canonical_manifest_sha256") != validated["hashes"]["canonical_manifest"]:
        raise ValueError("PIPELINE_BINDING_MANIFEST_MISMATCH")
    if int(binding.get("canonical_unique_product_count") or -1) != int(validated["manifest"].get("cumulative_unique_product_count") or 0):
        raise ValueError("PIPELINE_BINDING_PRODUCT_COUNT_MISMATCH")
    return binding


def _git_bytes(*args: str, check: bool = True, input_bytes: bytes | None = None, env=None) -> bytes:
    result = subprocess.run(["git", *args], check=check, input=input_bytes,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return result.stdout


def _remote_blob_sha(parent: str, repo_path: str) -> str:
    return hashlib.sha256(_git_bytes("show", f"{parent}:{repo_path}")).hexdigest()


def publish_binding(root: Path, binding: Dict[str, Any]) -> str:
    _git_bytes("fetch", "--depth=1", "origin", BRANCH)
    parent = _git_bytes("rev-parse", "FETCH_HEAD").decode().strip()
    checks = {
        "latest": "latest.json",
        "feed": "feed.json",
        "coverage_state": "coverage-state.json",
        "canonical_manifest": MANIFEST_RELATIVE,
    }
    for key, relative in checks.items():
        remote_sha = _remote_blob_sha(parent, PREFIX + relative)
        if remote_sha != str((binding.get("snapshot_inputs") or {}).get(key) or ""):
            raise ValueError(f"PIPELINE_REMOTE_GENERATION_CHANGED:{key}")

    binding_path = root / BINDING_NAME
    with tempfile.TemporaryDirectory() as directory:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(directory) / "index")}
        _git_bytes("read-tree", parent, env=env)
        blob = _git_bytes("hash-object", "-w", str(binding_path)).decode().strip()
        _git_bytes("update-index", "--add", "--cacheinfo", "100644", blob, PREFIX + BINDING_NAME, env=env)
        tree = _git_bytes("write-tree", env=env).decode().strip()
        message = f"Bind Brand64 daily snapshot to collection run {binding.get('collection_run_id')}\n".encode()
        commit = _git_bytes("commit-tree", tree, "-p", parent, input_bytes=message).decode().strip()
        _git_bytes("push", "origin", f"{commit}:refs/heads/{BRANCH}")
    return commit


def stamp_gemini(gemini_root: Path, direct_root: Path, *, analysis_run_id: str,
                 analysis_run_attempt: str = "", expected_collection_run_id: str = "") -> Dict[str, Any]:
    binding = verify_binding(direct_root, expected_collection_run_id=expected_collection_run_id)
    latest_path = _required(gemini_root, "latest.json")
    latest = read_json(latest_path)
    date = str(latest.get("latest_attempted_scan_date") or "")
    if date != binding.get("observation_date"):
        raise ValueError("PIPELINE_GEMINI_DATE_MISMATCH")
    raw_artifact = str(latest.get("artifact_path") or "")
    artifact_path = Path(raw_artifact)
    if not artifact_path.is_file():
        artifact_path = gemini_root / date / Path(raw_artifact).name
    artifact_path = _required(artifact_path.parent, artifact_path.name)
    artifact = read_json(artifact_path)
    input_snapshot = {
        "observation_date": binding["observation_date"],
        "collector": binding["collector"],
        "collection_run_id": binding["collection_run_id"],
        "collection_run_attempt": binding.get("collection_run_attempt") or "",
        "collector_source_sha": binding.get("collector_source_sha") or "",
        "canonical_manifest_sha256": binding["canonical_manifest_sha256"],
        "canonical_unique_product_count": binding["canonical_unique_product_count"],
        "observed_product_count_today": binding["observed_product_count_today"],
        "scan_status": binding["scan_status"],
        "snapshot_binding_sha256": sha256_file(direct_root / BINDING_NAME),
    }
    artifact.update({
        "analyzer": ANALYZER,
        "analysis_run_id": str(analysis_run_id),
        "analysis_run_attempt": str(analysis_run_attempt),
        "analysis_input_snapshot": input_snapshot,
        "pipeline_stage": "MD_ANALYSIS",
        "pipeline_binding_status": "BOUND_TO_CANONICAL_SNAPSHOT",
    })
    write_json(artifact_path, artifact)
    latest.update({
        "analyzer": ANALYZER,
        "analysis_run_id": str(analysis_run_id),
        "analysis_run_attempt": str(analysis_run_attempt),
        "source_collector": binding["collector"],
        "source_collection_run_id": binding["collection_run_id"],
        "analysis_input_snapshot_sha256": input_snapshot["snapshot_binding_sha256"],
        "analysis_input_manifest_sha256": binding["canonical_manifest_sha256"],
        "pipeline_binding_status": "BOUND_TO_CANONICAL_SNAPSHOT",
    })
    write_json(latest_path, latest)
    return latest


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-publish")
    create.add_argument("--root", type=Path, default=DIRECT_ROOT)
    create.add_argument("--date", default=None)
    create.add_argument("--collection-run-id", required=True)
    create.add_argument("--collection-run-attempt", default="")
    create.add_argument("--collector-source-sha", default="")

    verify = sub.add_parser("verify")
    verify.add_argument("--root", type=Path, default=DIRECT_ROOT)
    verify.add_argument("--date", default=None)
    verify.add_argument("--expected-collection-run-id", default="")

    stamp = sub.add_parser("stamp-gemini")
    stamp.add_argument("--direct-root", type=Path, default=DIRECT_ROOT)
    stamp.add_argument("--gemini-root", type=Path, default=GEMINI_ROOT)
    stamp.add_argument("--analysis-run-id", required=True)
    stamp.add_argument("--analysis-run-attempt", default="")
    stamp.add_argument("--expected-collection-run-id", default="")

    args = parser.parse_args()
    if args.command == "create-publish":
        binding = build_binding(
            args.root,
            expected_date=args.date,
            collection_run_id=args.collection_run_id,
            collection_run_attempt=args.collection_run_attempt,
            collector_source_sha=args.collector_source_sha,
        )
        commit = publish_binding(args.root, binding)
        print(json.dumps({"status": "BOUND", "collection_run_id": binding["collection_run_id"],
                          "canonical_manifest_sha256": binding["canonical_manifest_sha256"],
                          "canonical_unique_product_count": binding["canonical_unique_product_count"],
                          "published_commit": commit}, ensure_ascii=False))
        return 0
    if args.command == "verify":
        binding = verify_binding(args.root, expected_date=args.date,
                                 expected_collection_run_id=args.expected_collection_run_id)
        print(json.dumps({"status": "VALID", "collection_run_id": binding["collection_run_id"],
                          "canonical_manifest_sha256": binding["canonical_manifest_sha256"],
                          "canonical_unique_product_count": binding["canonical_unique_product_count"]}, ensure_ascii=False))
        return 0
    latest = stamp_gemini(
        args.gemini_root,
        args.direct_root,
        analysis_run_id=args.analysis_run_id,
        analysis_run_attempt=args.analysis_run_attempt,
        expected_collection_run_id=args.expected_collection_run_id,
    )
    print(json.dumps({"status": "STAMPED", "analysis_run_id": latest["analysis_run_id"],
                      "source_collection_run_id": latest["source_collection_run_id"],
                      "analysis_input_manifest_sha256": latest["analysis_input_manifest_sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
