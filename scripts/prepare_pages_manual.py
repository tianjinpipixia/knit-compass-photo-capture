#!/usr/bin/env python3
"""Prepare a source candidate only; never infer Pages settings, build or deploy."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def prepare(repository: Path, output: Path, code_commit: str, source_path: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", code_commit):
        raise ValueError("PAGES_CODE_COMMIT_INVALID")
    if source_path not in ("/", "/docs"):
        raise ValueError("PAGES_SOURCE_PATH_INVALID")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repository, stderr=subprocess.PIPE)

    if git("cat-file", "-t", code_commit).strip() != b"commit":
        raise ValueError("PAGES_SOURCE_NOT_COMMIT")
    try:
        git("merge-base", "--is-ancestor", code_commit, "refs/remotes/origin/main")
    except subprocess.CalledProcessError as exc:
        raise ValueError("PAGES_SOURCE_NOT_ON_MAIN") from exc
    prefix = "docs/" if source_path == "/docs" else ""
    git("cat-file", "-e", code_commit + ":" + prefix + "index.html")
    archive = git("archive", "--format=tar", code_commit, *(["--", "docs"] if prefix else []))
    receipt = {
        "format": "KC_PAGES_SOURCE_CANDIDATE_V1",
        "code_commit": code_commit,
        "source_path": source_path,
        "source_archive_sha256": hashlib.sha256(archive).hexdigest(),
        "pages_settings_verified": False,
        "ready_for_deployment": False,
        "publication_status": "ADMIN_CONFIGURATION_AND_RELEASE_APPROVAL_REQUIRED",
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "source.tar").write_bytes(archive)
    (output / "candidate.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--source-path", choices=["/", "/docs"], required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.repository, args.output, args.code_commit, args.source_path)))
