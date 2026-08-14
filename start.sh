#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"
PORT="${PORT:-8080}"
URL="http://127.0.0.1:${PORT}/"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python 3 was not found." >&2
  exit 1
fi

echo "Starting Knit Compass at ${URL}"

case "$(uname -s)" in
  Darwin)
    open "${URL}" >/dev/null 2>&1 || true
    ;;
  Linux)
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "${URL}" >/dev/null 2>&1 || true
    fi
    ;;
esac

exec "${PYTHON}" -m http.server "${PORT}" --bind 127.0.0.1
