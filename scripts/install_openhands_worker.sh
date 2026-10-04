#!/usr/bin/env bash
set -euo pipefail

ROOT="${SIGMA_ROOT:-/opt/ai-command-center}"
STACK_DIR="$ROOT/deploy/sigma-stack"
STATE_DIR="${OPENHANDS_STATE_DIR:-/opt/sigma/openhands/state}"
PROJECTS_DIR="${OPENHANDS_PROJECTS_DIR:-/opt/sigma/openhands/projects}"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed." >&2
  exit 1
fi

docker compose version >/dev/null

if [ ! -d "$ROOT/.git" ]; then
  echo "ERROR: Sigma repository not found at $ROOT" >&2
  exit 1
fi

mkdir -p "$STATE_DIR" "$PROJECTS_DIR"

cd "$ROOT"
git fetch origin
git pull --ff-only

cd "$STACK_DIR"

docker compose \
  --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.openhands.yml \
  pull openhands

docker compose \
  --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.openhands.yml \
  up -d openhands

echo
echo "OpenHands container status:"
docker compose \
  --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.openhands.yml \
  ps openhands

echo
echo "Local health probe:"
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:"${OPENHANDS_PORT:-8000}"/ >/dev/null
echo "PASS: OpenHands is responding on loopback port ${OPENHANDS_PORT:-8000}."
echo
echo "It is intentionally NOT public. Use an SSH tunnel or a protected reverse proxy to access the UI."
