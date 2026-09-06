#!/usr/bin/env python3
"""Exercise save completion and failure against the actual capture save handler."""
import subprocess
from pathlib import Path
from tooling import require_node

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([require_node(), "--test", str(ROOT / "tests/test_capture_save_lifecycle.js")], cwd=ROOT, check=True)
