#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "${ROOT}"
export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
  echo "ERROR: Mac validation must run on Apple Silicon arm64." >&2
  exit 1
fi

PYTHON=python3
if [ -x .venv/bin/python ]; then
  PYTHON=.venv/bin/python
fi

"${PYTHON}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else "Python 3.9+ is required")'
"${PYTHON}" -c 'import yaml'
"${PYTHON}" -c 'import sys; sys.path.insert(0, "scripts"); from tooling import require_node; require_node()'

for validator in scripts/validate_*.py; do
  echo "RUN ${validator}"
  "${PYTHON}" "${validator}"
done

echo "Apple Silicon validation passed."
