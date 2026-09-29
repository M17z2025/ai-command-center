#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose --env-file deploy/sigma-stack/.env -f deploy/sigma-stack/docker-compose.yml -f deploy/sigma-stack/docker-compose.ollama.yml -f deploy/sigma-stack/docker-compose.automation.yml)
for service in sigma-runner sigma-intake; do
  id="$("${compose[@]}" ps -q "$service")"
  # Missing/stopped services remain an operator decision, not silently activated.
  [[ -n "$id" ]] || continue
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$id")"
  if [[ "$health" == unhealthy ]]; then
    logger -t sigma-watchdog "Restarting unhealthy $service"
    "${compose[@]}" restart "$service"
  fi
done
