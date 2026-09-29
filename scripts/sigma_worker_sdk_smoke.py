"""Offline smoke of the exact SDK constructors used by the disposable worker."""
from pathlib import Path
from openhands.sdk import Conversation, LocalWorkspace
from sigma_worker_sandbox import build_agent


agent = build_agent({"model": "sigma-ci-offline"})
with LocalWorkspace(working_dir=Path("/workspace")) as workspace:
    conversation = Conversation(agent=agent, workspace=workspace)
    try:
        assert conversation.state is not None
        print("OpenHands Agent, LLM, LocalWorkspace and Conversation constructors passed")
    finally:
        conversation.close()
