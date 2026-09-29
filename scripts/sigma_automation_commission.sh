#!/usr/bin/env bash
# Run only on the approved OVH host, from an exact reviewed Git checkout.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 - "$ROOT" "$@" <<'PY'
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import urllib.request

REPO = "M17z2025/ai-command-center"
PROJECT = "sigma-stack"
ROOT = Path(sys.argv[1]).resolve()
STATE_DIR = Path("/opt/sigma-automation-commission")
parser = argparse.ArgumentParser(description="Preflight or commission Sigma automation on the existing OVH stack.")
parser.add_argument("--sha", required=True, help="Exact reviewed 40-character source SHA")
parser.add_argument("--env-file", default="/opt/ai-command-center/deploy/sigma-stack/.env")
parser.add_argument("--mode", choices=["plan", "worker-readonly"], default="plan")
parser.add_argument("--ci-run", action="append", required=True, type=int, help="Exact-source successful GitHub run ID; repeat for all three required workflows")
parser.add_argument("--security-source-reviewed", help="Operator attestation: exact SHA covered by independent worker-isolation source review")
parser.add_argument("--security-evidence", help="GitHub URL of the independent worker-isolation source review report")
parser.add_argument("--apply", action="store_true", help="Build and start selected services after all preflights pass")
args = parser.parse_args(sys.argv[2:])

def fail(message):
    raise SystemExit("COMMISSION_BLOCKED: " + message)

def run(argv, **kwargs):
    result = subprocess.run(argv, text=True, capture_output=True, timeout=kwargs.pop("timeout", 60), **kwargs)
    if result.returncode:
        # Docker/Git errors can contain credentials. Do not copy captured output to logs.
        fail("command failed: " + argv[0] + " " + argv[1] + " (output withheld)")
    return result.stdout.strip()

def report(kind, **fields):
    print(json.dumps({"kind": kind, **fields}, sort_keys=True), flush=True)

if not re.fullmatch(r"[0-9a-f]{40}", args.sha):
    fail("--sha must be an exact lowercase commit SHA")
if run(["git", "-C", str(ROOT), "rev-parse", "HEAD"]) != args.sha:
    fail("checkout does not match approved source SHA")
if run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=normal"]):
    fail("reviewed checkout must have no modified or untracked files")
if STATE_DIR.resolve().is_relative_to(ROOT):
    fail("commission state must remain outside the reviewed source directory")
env_path = Path(args.env_file)
if env_path.resolve().is_relative_to(ROOT):
    fail("use a separate reviewed source checkout so protected configuration stays outside the image build context")
if env_path.is_symlink() or not env_path.is_file():
    fail("protected env file missing or is a symlink")
try:
    metadata = env_path.stat()
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        fail("protected env file must have no group/other permissions (0600 or stricter)")
    if metadata.st_size > 1048576:
        fail("protected env file exceeds size limit")
    lines = env_path.read_text(encoding="utf-8").splitlines()
except PermissionError:
    fail("protected env file is unreadable; a privileged operator must provision and run this helper")
values = {}
for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    match = re.fullmatch(r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)", line)
    if not match:
        fail("env file must contain single-line KEY=value assignments")
    key, raw = match.groups()
    if key in values:
        fail("duplicate environment key: " + key)
    # No shell evaluation or interpolation. Complex dotenv constructs must be normalized privately.
    if "$" in raw or "\x00" in raw:
        fail("environment interpolation is unsupported: " + key)
    try:
        parts = shlex.split(raw, comments=True, posix=True)
    except ValueError:
        fail("invalid environment quoting: " + key)
    if len(parts) > 1:
        fail("quote environment values containing spaces: " + key)
    values[key] = parts[0] if parts else ""

required = ["OLLAMA_MODEL"]
if args.mode == "worker-readonly":
    required += ["SIGMA_RUNTIME_TOKEN", "SIGMA_MEMORY_TOKEN", "SIGMA_WORKER_TOKEN",
                 "SIGMA_WEBHOOK_SECRET", "OLLAMA_WORKER_MODEL", "OLLAMA_EMBEDDING_MODEL",
                 "SIGMA_LLM_ENDPOINT", "SIGMA_LLM_MODEL"]
missing = [key for key in required if not values.get(key)]
for key in required:
    report("required_configuration", name=key, present=bool(values.get(key)))
if missing:
    fail("missing required configuration: " + ", ".join(missing))
for key in ["SIGMA_RUNNER_EXECUTE", "SIGMA_RUNNER_ALLOW_WRITE",
            "SIGMA_WORKER_ALLOW_WRITE", "SIGMA_AUTOMATION_REPORT_WRITE"]:
    if values.get(key, "0") not in {"0", "false", "False", ""}:
        fail(key + " must remain disabled during commissioning")
token = values.get("SIGMA_AUTOMATION_GITHUB_TOKEN", "")

def github(path):
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "sigma-commission"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request("https://api.github.com/repos/" + REPO + path,
        headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except Exception:
        fail("GitHub evidence or repository read access unavailable; verify public access or the read-only credential")

if github("/commits/" + args.sha).get("sha") != args.sha:
    fail("source commit cannot be verified in the approved repository")
required_workflows = {"Sigma automation and container", "Sigma mesh runtime", "Sigma control-plane validation"}
if args.mode == "worker-readonly":
    required_workflows.add("Sigma worker isolation")
seen = set()
for run_id in args.ci_run:
    evidence = github("/actions/runs/" + str(run_id))
    if evidence.get("head_sha") != args.sha or evidence.get("conclusion") != "success" or evidence.get("status") != "completed":
        fail("CI run is not successful on the exact reviewed SHA: " + str(run_id))
    seen.add(evidence.get("name"))
    report("verified_ci", run_id=run_id, url=evidence.get("html_url"), source_sha=args.sha)
if required_workflows - seen:
    fail("missing successful exact-source workflows: " + ", ".join(sorted(required_workflows - seen)))
if args.mode == "worker-readonly":
    if args.security_source_reviewed != args.sha:
        fail("worker-readonly needs explicit attestation of independent isolation source review for this exact SHA")
    if not args.security_evidence or not args.security_evidence.startswith("https://github.com/" + REPO + "/"):
        fail("provide the independent source-review report URL in the approved repository")
    report("security_review_attestation", url=args.security_evidence, source_sha=args.sha,
           evidence_verified_by="operator", release_authority_granted=False)

ids = run(["docker", "ps", "-q", "--filter", "label=com.docker.compose.project=" + PROJECT,
           "--filter", "label=com.docker.compose.service=sigma-runtime"]).split()
if len(ids) != 1:
    fail("expected exactly one existing running Sigma runtime")
runtime = json.loads(run(["docker", "inspect", ids[0]]))[0]
labels = runtime.get("Config", {}).get("Labels", {})
if labels.get("com.docker.compose.project.working_dir") != "/opt/ai-command-center/deploy/sigma-stack":
    fail("existing Compose working directory differs from audited deployment")
network = PROJECT + "_sigma-private"
run(["docker", "network", "inspect", network])
if args.mode == "worker-readonly":
    version = run(["docker", "version", "--format", "{{.Server.Version}}"])
    if not re.match(r"^\d+\.", version) or int(version.split(".", 1)[0]) < 28:
        fail("worker isolation requires Docker Engine 28 or later")
    drivers = json.loads(run(["docker", "info", "--format", "{{json .Plugins.Network}}"] ))
    if "bridge" not in drivers:
        fail("Docker bridge networking unavailable for isolated inference")
    existing = subprocess.run(["docker", "network", "inspect", "sigma-worker-inference"],
                              capture_output=True, text=True, timeout=30)
    if existing.returncode == 0:
        isolated = json.loads(existing.stdout)[0]
        if (not isolated.get("Internal") or isolated.get("Driver") != "bridge"
                or isolated.get("Options", {}).get("com.docker.network.bridge.gateway_mode_ipv4") != "isolated"):
            fail("existing worker inference network does not satisfy reviewed isolation")
ollama_ids = run(["docker", "ps", "-q", "--filter", "label=com.docker.compose.project=" + PROJECT,
                  "--filter", "label=com.docker.compose.service=ollama"]).split()
if len(ollama_ids) != 1:
    fail("expected exactly one running private Ollama service")
model_rows = run(["docker", "exec", ollama_ids[0], "ollama", "list"]).splitlines()[1:]
models = {line.split()[0] for line in model_rows if line.split()}
for key in ["OLLAMA_MODEL"] + (["OLLAMA_WORKER_MODEL", "OLLAMA_EMBEDDING_MODEL"] if args.mode == "worker-readonly" else []):
    if values[key] not in models:
        fail(key + " is not installed; this helper will not pull models")
report("preflight_pass", source_sha=args.sha, mode=args.mode, apply=args.apply,
       existing_project=PROJECT, paid_fallback=False, execution_enabled=False)
if not args.apply:
    raise SystemExit(0)

# Build only reviewed local source, retain existing runtime/memory/Ollama containers and volumes.
def build(dockerfile, name):
    tag = "sigma-reviewed/" + name + ":" + args.sha
    # Archive only tracked bytes from the exact commit. Ignored local files/secrets
    # cannot enter Docker's context, regardless of .dockerignore patterns.
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", args.sha],
                             capture_output=True, timeout=60)
    if archive.returncode:
        fail("cannot export reviewed source archive")
    built = subprocess.run(["docker", "build", "--label", "org.opencontainers.image.revision=" + args.sha,
                            "-f", dockerfile, "-t", tag, "-"],
                           input=archive.stdout, capture_output=True, timeout=1800)
    if built.returncode:
        fail("reviewed image build failed: " + name + " (output withheld)")
    image_id = run(["docker", "image", "inspect", "--format", "{{.Id}}", tag])
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        fail("built image has no immutable ID")
    report("reviewed_image", component=name, source_sha=args.sha, image_id=image_id)
    return image_id

automation_image = build("Dockerfile.sigma-automation", "automation")
runner_env = {
    "SIGMA_RUNTIME_PROVIDER": "http", "SIGMA_LLM_ENDPOINT": "http://ollama:11434/api/chat",
    "SIGMA_LLM_PROTOCOL": "ollama-chat", "SIGMA_LLM_MODEL": values["OLLAMA_MODEL"],
    "SIGMA_RUNTIME_DB": "/data/sigma-runtime.db", "SIGMA_GITHUB_TOKEN": token,
    "SIGMA_RUNNER_EXECUTE": "0", "SIGMA_RUNNER_ALLOW_WRITE": "0",
    "SIGMA_WORKER_ENDPOINT": "", "SIGMA_WORKER_TOKEN": "",
    "SIGMA_AUTOMATION_REPORT_WRITE": "0", "SIGMA_GSTACK_CACHE": "/opt/sigma-gstack",
}
for key in ["SIGMA_LLM_TIMEOUT_SECONDS", "SIGMA_LLM_MAX_TOKENS", "SIGMA_LLM_CONTEXT_TOKENS",
            "SIGMA_LLM_DISABLE_THINKING", "SIGMA_MAX_PARALLEL_SPECIALISTS",
            "SIGMA_RUNNER_INTERVAL_SECONDS", "SIGMA_AUTOMATION_JOB_TIMEOUT"]:
    if key in values:
        runner_env[key] = values[key]
service = {
    "image": automation_image, "command": ["python", "scripts/sigma_automation.py", "worker"],
    "restart": "unless-stopped", "init": True, "read_only": True, "cap_drop": ["ALL"],
    "pids_limit": 128, "mem_limit": "1g", "stop_grace_period": "30s",
    "tmpfs": ["/tmp:size=64m,mode=1777"], "environment": runner_env,
    "volumes": ["sigma-automation-data:/data"], "networks": ["sigma-private"],
    "security_opt": ["no-new-privileges:true"],
    "healthcheck": {"test": ["CMD", "python", "scripts/sigma_automation.py", "health"],
                    "interval": "30s", "timeout": "10s", "retries": 3, "start_period": "60s"},
}
compose = {"services": {"sigma-runner": service},
           "networks": {"sigma-private": {"external": True, "name": network}},
           "volumes": {"sigma-automation-data": {"name": PROJECT + "_sigma-automation-data"}}}
if args.mode == "worker-readonly":
    # Existing reviewed isolation overlay is mandatory; fail closed rather than using the legacy worker.
    sandbox = build("Dockerfile.sigma-worker-sandbox", "worker-sandbox")
    gateway = build("Dockerfile.sigma-worker-gateway", "worker-gateway")
    worker = build("Dockerfile.sigma-worker", "worker")
    merged_env = dict(os.environ, **values,
                      SIGMA_WORKER_SANDBOX_IMAGE=sandbox, SIGMA_WORKER_GATEWAY_IMAGE=gateway,
                      SIGMA_DOCKER_GID=str(Path("/var/run/docker.sock").stat().st_gid))
    cmd = ["docker", "compose", "--project-name", PROJECT, "--env-file", str(env_path)]
    for filename in ["docker-compose.yml", "docker-compose.ollama.yml",
                     "docker-compose.memory.yml", "docker-compose.automation.yml",
                     "docker-compose.worker-isolation.yml"]:
        cmd += ["-f", str(ROOT / "deploy/sigma-stack" / filename)]
    merged = json.loads(run(cmd + ["config", "--format", "json"], env=merged_env))
    # Carry only newly commissioned services; no depends_on expansion or existing-stack migration.
    selected = ["sigma-worker", "inference-gateway", "sigma-intake"]
    for name in selected:
        part = merged.get("services", {}).get(name)
        if not part:
            fail("reviewed isolation service missing: " + name)
        part.pop("build", None)
        part.pop("depends_on", None)
        part["image"] = {"sigma-worker": worker, "inference-gateway": gateway,
                         "sigma-intake": automation_image}[name]
        compose["services"][name] = part
    compose["services"]["sigma-worker"]["environment"]["SIGMA_WORKER_ALLOW_WRITE"] = "0"
    # Only the dedicated reader credential reaches the broker; no writer credential is used.
    compose["services"]["sigma-worker"]["environment"]["SIGMA_GITHUB_TOKEN"] = token
    for name, definition in merged.get("networks", {}).items():
        if name != "sigma-private":
            compose["networks"][name] = definition
    for name, definition in merged.get("volumes", {}).items():
        if name == "sigma-worker-workspaces":
            compose["volumes"][name] = definition

# Persist private, reproducible selected-service manifest outside the reviewed checkout.
state_dir = STATE_DIR
state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
if state_dir.is_symlink() or stat.S_IMODE(state_dir.stat().st_mode) & 0o077:
    fail("commission state directory must be private and not a symlink")
manifest = state_dir / (args.sha + "-" + args.mode + ".json")
if manifest.is_symlink():
    fail("commission manifest must not be a symlink")
fd = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
os.fchmod(fd, 0o600)
with os.fdopen(fd, "w") as handle:
    json.dump(compose, handle)
command = ["docker", "compose", "--project-name", PROJECT, "-f", str(manifest)]
run(command + ["config", "--quiet"])
# Same project/service identity replaces only the old scheduler. Never --remove-orphans/down/-v.
run(command + ["up", "-d", "--no-build", "--no-deps", "--wait", "--wait-timeout", "180",
               *compose["services"]], timeout=240)
report("commissioned", source_sha=args.sha, mode=args.mode, services=list(compose["services"]),
       manifest=str(manifest), execution_enabled=False, webhook_public_route_configured=False)
PY
