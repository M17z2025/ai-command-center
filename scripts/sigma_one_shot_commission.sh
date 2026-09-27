#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK="$ROOT/deploy/sigma-stack"
ENV_FILE="$STACK/.env"
COMPOSE=(
  docker compose --env-file "$ENV_FILE"
  -f "$STACK/docker-compose.yml"
  -f "$STACK/docker-compose.ollama.yml"
  -f "$STACK/docker-compose.memory.yml"
)

cd "$ROOT"

echo "[1/6] Stopping portfolio runner during commissioning..."
"${COMPOSE[@]}" stop sigma-runner >/dev/null || true

echo "[2/6] Ensuring runtime and memory services are current..."
"${COMPOSE[@]}" up -d --build sigma-runtime sigma-memory >/dev/null

echo "[3/6] Running evidence-gated lesson promotion..."
"${COMPOSE[@]}" exec -T sigma-runtime   python scripts/sigma_one_shot_commission.py --db /data/sigma-runtime.db prepare

echo "[4/6] Restarting memory and runtime to prove persistence..."
"${COMPOSE[@]}" restart sigma-memory sigma-runtime >/dev/null
sleep 8

echo "[5/6] Verifying post-restart retrieval..."
"${COMPOSE[@]}" exec -T sigma-runtime   python scripts/sigma_one_shot_commission.py --db /data/sigma-runtime.db verify

echo "[6/6] Restarting portfolio runner in configured planning/execution mode..."
"${COMPOSE[@]}" up -d sigma-runner >/dev/null

echo
echo "SIGMA_ONE_SHOT_COMMISSIONING_PASS"
"${COMPOSE[@]}" ps
