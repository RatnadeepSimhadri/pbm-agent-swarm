"""Deployment runner with human-in-the-loop approval gate.

This runner does not call any LLM. It lists workspace artifacts, waits for
human approval via an asyncio.Event, then copies files into the seed app.
Used by both mock and real (Claude) pipelines.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Any

from app.agents.runner import AgentRunner
from app.events import EventBus
from app.models import EventType, PipelineEvent, PipelineState, PipelineTask, TaskStatus
from app.workspace import Workspace

logger = logging.getLogger(__name__)


class DeployRunner(AgentRunner):
    def __init__(self, workspace: Workspace, seed_app_path: str):
        self.workspace = workspace
        self.seed_app_path = os.path.abspath(seed_app_path)
        self.approval_event = asyncio.Event()
        self.approved: bool | None = None

    async def run(
        self,
        pipeline: PipelineState,
        task: PipelineTask,
        event_bus: EventBus,
    ) -> dict[str, Any]:
        agent = task.agent.value

        # Build file manifest from workspace
        files = self.workspace.list_files()
        manifest = []
        for f in files:
            try:
                content = self.workspace.read_file(f)
                manifest.append({
                    "path": f,
                    "lines": len(content.splitlines()),
                })
            except Exception:
                manifest.append({"path": f, "lines": 0})

        # Stream a summary to the agent output
        summary = f"## Deployment Review\n\n"
        summary += f"**{len(manifest)} files** ready to deploy to seed-app:\n\n"
        for item in manifest:
            summary += f"- `{item['path']}` ({item['lines']} lines)\n"
        summary += f"\nAwaiting human approval...\n"

        await event_bus.emit(PipelineEvent(
            type=EventType.AGENT_OUTPUT,
            agent=agent,
            data={"content": summary, "done": False},
        ))

        # Emit approval request with manifest
        await event_bus.emit(PipelineEvent(
            type=EventType.DEPLOY_APPROVAL_REQUESTED,
            agent=agent,
            data={"files": manifest},
        ))

        # Update task status to waiting_approval
        task.status = TaskStatus.WAITING_APPROVAL
        await event_bus.emit(PipelineEvent(
            type=EventType.TASK_STATE_CHANGE,
            agent=agent,
            data={
                "task_id": task.id,
                "status": task.status.value,
                "display_name": task.display_name,
                "started_at": task.started_at,
                "completed_at": None,
                "error": None,
            },
        ))

        # Wait for human decision
        await self.approval_event.wait()

        if self.approved:
            # Copy workspace files to seed-app
            deployed = []
            for item in manifest:
                src = Path(self.workspace.root) / item["path"]
                dst = Path(self.seed_app_path) / item["path"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                deployed.append(item["path"])
                logger.info("Deployed: %s -> %s", src, dst)

            result_msg = f"\n\nDeployed **{len(deployed)} files** to seed-app successfully.\n"
            await event_bus.emit(PipelineEvent(
                type=EventType.AGENT_OUTPUT,
                agent=agent,
                data={"content": result_msg, "done": True},
            ))
            await event_bus.emit(PipelineEvent(
                type=EventType.DEPLOY_RESULT,
                agent=agent,
                data={"status": "deployed", "files_deployed": len(deployed)},
            ))

            return {
                "output": summary + result_msg,
                "artifacts": deployed,
                "tokens_used": 0,
                "lines_written": 0,
            }
        else:
            reject_msg = "\n\nDeployment **rejected** by user. No files were modified.\n"
            await event_bus.emit(PipelineEvent(
                type=EventType.AGENT_OUTPUT,
                agent=agent,
                data={"content": reject_msg, "done": True},
            ))
            await event_bus.emit(PipelineEvent(
                type=EventType.DEPLOY_RESULT,
                agent=agent,
                data={"status": "rejected", "files_deployed": 0},
            ))

            return {
                "output": summary + reject_msg,
                "artifacts": [],
                "tokens_used": 0,
                "lines_written": 0,
            }
