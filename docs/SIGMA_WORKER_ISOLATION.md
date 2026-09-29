# Credential-free worker execution

The private worker service is now a trusted Git/Docker broker. It does not import
the model SDK, run repository commands, or expose credentials to repository code.
The existing authority and repository allowlist gates still apply.

## Boundaries

1. Require the mission's full `source_sha`; fetch that exact commit and verify it.
   Reject source symlinks and submodules before checkout. Disable Git hooks,
   credential helpers, global/system config, recursive submodules and local/ext
   transports. Credentials are passed only to broker Git transport and PR calls.
2. Send regular source files, without `.git`, to a disposable non-root container
   by stdin. There are no host mounts, Docker socket, credential environment
   variables, published ports or inherited host process environment in the job.
   Drop capabilities, enable no-new-privileges, and bound memory, CPU, PIDs,
   writable storage, output and wall time. The image must be an immutable digest.
3. Model execution reaches only a dedicated inference gateway. Require an
   internal IPv4 Docker bridge with `gateway_mode_ipv4=isolated`, no IPv6, and
   exactly one existing peer: the approved gateway image. Use a static gateway
   host entry and loopback DNS. The gateway exposes only chat/generate/show for
   the one commissioned Ollama model; no pull, push, create, delete or redirects.
4. Parse bounded untrusted file-change JSON. Reject duplicate keys, path traversal,
   links, path conflicts, Git metadata and authority/control-path modifications.
   Apply accepted bytes to a **second freshly fetched exact-SHA checkout**.
5. Run the registered verification command in a separate disposable container
   with network `none`. Check its exit through the Docker daemon, never an
   agent's reported test result. Discard the verifier filesystem.
6. Only the broker stages, commits and pushes its generated Sigma branch and
   opens a PR. Passing tests does not authorize merging, release or deployment.

The Docker socket grants the trusted broker host-level power. Keep it private,
and never attach untrusted code or credentials to the inference gateway. The
sandbox image and gateway image IDs are deployment approvals, not request input.

Docker documents why `internal` alone still permits host gateway access, and
why isolated gateway mode is required: [network internal mode](https://docs.docker.com/reference/cli/docker/network/create/)
and [isolated gateway mode](https://docs.docker.com/engine/network/port-publishing/).
Docker Engine 28 or newer is needed for this network mode.

## Commissioning

Build `Dockerfile.sigma-worker`, `Dockerfile.sigma-worker-sandbox` and
`Dockerfile.sigma-worker-gateway` from the reviewed commit. Record the resulting
image IDs. Set `SIGMA_WORKER_SANDBOX_IMAGE`, `SIGMA_WORKER_GATEWAY_IMAGE` and
`SIGMA_DOCKER_GID` using those images and the host socket group. Add
`docker-compose.worker-isolation.yml` after the existing OVH compose overlays.
The broker remains non-root and its existing `SIGMA_WORKER_ALLOW_WRITE` defaults
to `0`. The broker rejects unsupported/uncommissioned networks and missing pins.

Run this real Docker proof on the host before enabling write mode:

```sh
docker build -f tests/Dockerfile.worker-isolation-fixture -t sigma-isolation-fixture .
export SIGMA_WORKER_ISOLATION_TEST_IMAGE="$(docker image inspect sigma-isolation-fixture --format '{{.Id}}')"
python -m unittest discover -s tests -p test_sigma_worker_isolation.py
```

This uses the production executor and Docker boundary with real adversarial
processes. It needs no model, token, or paid inference. It checks credential and
host-path isolation, read-only root, forged success, independent verification,
and actual inference-only versus host/internet connectivity. Ordinary local
unit runs explicitly skip these Docker tests unless the image is supplied.

Attach exact commit/image IDs, the complete test result, network inspection and
a real bounded model mission's source/branch/test/PR evidence to issue #97 before
calling unattended writes commissioned. No live OVH or live model proof is
claimed by adding source or passing CI.

## Current deliberate limits

- Only the command-center verification command is registered. Other products
  need reviewed toolchain images and verification profiles.
- Source symlinks/submodules and automatic edits to `.github`, `.sigma`,
  `headquarters`, agent control files and Git attributes/modules are blocked.
- Offline verification cannot install dependencies; bake approved dependencies
  into the pinned sandbox image.
- Every job carries its trusted broker label. Before accepting missions after
  restart, the broker removes its labelled orphan jobs. Multiple broker services
  on one Docker host must use separate `SIGMA_WORKER_BROKER_ID` values. Never
  infer success from a previous workspace or model transcript.
- Independent security review and actual host commissioning remain required.
