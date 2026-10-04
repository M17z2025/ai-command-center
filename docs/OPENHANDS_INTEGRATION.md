# OpenHands execution layer for Sigma

## Status

This integration installs OpenHands Agent Canvas as an isolated execution service beside the Sigma runtime. It does **not** by itself make Sigma autonomous. The Sigma-to-OpenHands dispatcher remains a separate integration gate.

## Architecture

```text
User
  -> Sigma supervisor/runtime
      -> future Sigma/OpenHands dispatcher
          -> OpenHands Agent Canvas
              -> /projects workspace only
              -> code / shell / tests
              -> GitHub
      -> Sigma critic / verification
```

## Security boundary

OpenHands can execute shell commands and modify files visible to it. Therefore:

- bind the UI to `127.0.0.1` only;
- mount only the dedicated OpenHands project directory at `/projects`;
- do not mount `/opt/ai-command-center`, `/root`, `/etc`, Docker sockets, SSH directories, or production secret directories;
- keep credentials out of the repository;
- expose remote access only through SSH tunnelling or an authenticated reverse proxy.

## Install on the OVH VPS

The Sigma repo is expected at `/opt/ai-command-center`.

```bash
cd /opt/ai-command-center
git pull --ff-only

# Add the OPENHANDS_* values from openhands.env.example to deploy/sigma-stack/.env
chmod +x scripts/install_openhands_worker.sh
./scripts/install_openhands_worker.sh
```

The service binds to `127.0.0.1:8000` by default. Agent Canvas state and project workspaces persist in dedicated Docker volumes, keeping them separate from the Sigma host filesystem.

## Access from another machine

Use an SSH tunnel rather than opening port 8000 publicly:

```bash
ssh -L 8000:127.0.0.1:8000 root@YOUR_OVH_HOST
```

Then open `http://127.0.0.1:8000/canvas` locally.

## Verification gates

OpenHands is not considered operational for Sigma until all of the following are evidenced:

1. Container is running.
2. Loopback HTTP endpoint responds.
3. A disposable test repository is placed under the dedicated project workspace.
4. OpenHands can inspect it.
5. OpenHands makes a controlled code change.
6. Tests run.
7. Git diff/commit evidence exists.
8. Sigma receives machine-readable execution status.
9. Sigma critic independently verifies the result.

Only gates 1-2 are installation gates. Gates 3-9 are the subsequent Sigma dispatcher/integration work.
