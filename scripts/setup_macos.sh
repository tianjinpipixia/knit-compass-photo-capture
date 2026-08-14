#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "${ROOT}"
export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "ERROR: This setup is for macOS." >&2
  exit 1
fi
if [ "$(uname -m)" != "arm64" ]; then
  echo "ERROR: Apple Silicon arm64 is required for the primary development environment." >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python 3 was not found." >&2
  exit 1
fi

python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else "Python 3.9+ is required")'

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js was not found." >&2
  echo "Install the Apple Silicon arm64 Node.js LTS build from https://nodejs.org/ and rerun this script." >&2
  exit 1
fi

NODE_ARCH=$(node -p 'process.arch')
if [ "${NODE_ARCH}" != "arm64" ]; then
  echo "ERROR: Intel Node.js is active. Install the Apple Silicon arm64 build; do not use Rosetta." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-validation.txt -r requirements-catalog.txt

echo "Mac development environment is ready."
echo "Run: scripts/validate_macos.sh"
