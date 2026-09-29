"""Disposable, credential-free executor. Its output is always untrusted."""
from __future__ import annotations
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile


def snapshot(root):
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("Links cannot leave sandbox")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def edit(root, request):
    from pydantic import SecretStr
    from openhands.sdk import Agent, Conversation, LLM, LocalWorkspace
    from openhands.sdk.tool import Tool
    from openhands.tools.preset.default import register_default_tools
    from openhands.tools.terminal import TerminalTool
    llm = LLM(usage_id="sigma-sandbox", model="ollama_chat/" + request["model"],
              base_url="http://inference-gateway:8081", api_key=SecretStr("local"),
              reasoning_effort="none", num_retries=1, timeout=300)
    register_default_tools(enable_browser=False)
    agent = Agent(llm=llm, tools=[Tool(name=TerminalTool.name)],
                  system_prompt_kwargs={"cli_mode": True})
    with LocalWorkspace(working_dir=root) as workspace:
        conversation = Conversation(agent=agent, workspace=workspace)
        try:
            conversation.send_message(request["prompt"])
            conversation.run()
        finally:
            conversation.close()


def main():
    incoming = sys.stdin.buffer.read(64 * 1024 * 1024 + 1)
    if len(incoming) > 64 * 1024 * 1024:
        raise RuntimeError("Input exceeds sandbox budget")
    with tarfile.open(fileobj=io.BytesIO(incoming)) as package:
        request = json.load(package.extractfile("request.json"))
        source = package.extractfile("source.tar").read()
    root = Path("/workspace")
    with tarfile.open(fileobj=io.BytesIO(source)) as tar:
        tar.extractall(root, filter="data")
    os.chdir(root)
    if request["mode"] == "verify":
        # Verification has no model/network and its modifications are discarded.
        result = subprocess.run(request["command"], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=request.get("timeout", 900))
        raise SystemExit(result.returncode)
    original = snapshot(root)
    # SDK output is not evidence and must not interleave with the transfer document.
    with open(os.devnull, "w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        edit(root, request)
    current = snapshot(root)
    changes = {path: (base64.b64encode(current[path]).decode() if path in current else None)
               for path in original.keys() | current.keys() if original.get(path) != current.get(path)}
    print(json.dumps(changes))


if __name__ == "__main__":
    main()
