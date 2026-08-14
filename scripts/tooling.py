#!/usr/bin/env python3
"""Shared development-tool discovery with Apple Silicon safety checks."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


def require_node(minimum_major: int = 18) -> str:
    configured = os.environ.get("KC_NODE", "").strip()
    node = shutil.which(configured) if configured else shutil.which("node")
    if not node:
        raise SystemExit(
            "ERROR: Node.js is required for JavaScript validation. "
            "On Apple Silicon, install the arm64 Node.js LTS build and rerun "
            "scripts/validate_macos.sh."
        )
    path = Path(node).expanduser()
    if not path.is_file():
        raise SystemExit(f"ERROR: Node.js executable was not found: {path}")
    result = subprocess.run(
        [str(path), "-p", "JSON.stringify({version:process.versions.node,arch:process.arch})"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise SystemExit(f"ERROR: Node.js could not run: {result.stderr.strip()}")
    try:
        metadata = json.loads(result.stdout)
        major = int(str(metadata["version"]).split(".", 1)[0])
        architecture = str(metadata["arch"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit("ERROR: Node.js returned invalid runtime metadata") from error
    if major < minimum_major:
        raise SystemExit(f"ERROR: Node.js {minimum_major}+ is required; found {metadata['version']}")
    if platform.system() == "Darwin" and platform.machine() == "arm64" and architecture != "arm64":
        raise SystemExit(
            "ERROR: Intel Node.js is running through Rosetta. "
            "Install the Apple Silicon arm64 Node.js LTS build."
        )
    return str(path)
