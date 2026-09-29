#!/usr/bin/env bash
set -euo pipefail
# Resolve only the existing project's services. Health recovery needs no secret
# environment file and works with the commissioning manifest's exact image IDs.
for service in sigma-runner sigma-intake; do
  ids=()
  mapfile -t ids < <(docker ps -aq --filter label=com.docker.compose.project=sigma-stack --filter "label=com.docker.compose.service=$service")
  # Missing/stopped services remain an operator decision, not silently activated.
  [[ ${#ids[@]} -eq 1 ]] || continue
  id="${ids[0]}"
  [[ "$(docker inspect --format '{{.State.Running}}' "$id")" == true ]] || continue
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$id")"
  if [[ "$health" == unhealthy ]]; then
    logger -t sigma-watchdog "Restarting unhealthy $service"
    docker restart "$id" >/dev/null
  fi
done
