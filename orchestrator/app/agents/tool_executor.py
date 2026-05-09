"""Executes agent tool calls against the workspace and seed app."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from app.events import EventBus
from app.models import EventType, PipelineEvent
from app.workspace import Workspace

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, workspace: Workspace, seed_app_path: str):
        self.workspace = workspace
        self.seed_app_path = Path(seed_app_path).resolve()

    async def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        agent: str,
        event_bus: EventBus,
    ) -> str:
        """Execute a tool call and return the result as a string."""
        await event_bus.emit(PipelineEvent(
            type=EventType.TOOL_CALL,
            agent=agent,
            data={"tool": tool_name, "arguments": tool_input},
        ))

        try:
            if tool_name == "read_file":
                return await self._read_file(tool_input["path"])
            elif tool_name == "write_file":
                return await self._write_file(tool_input["path"], tool_input["content"], agent, event_bus)
            elif tool_name == "edit_file":
                return await self._edit_file(tool_input["path"], tool_input["old_string"], tool_input["new_string"], agent, event_bus)
            elif tool_name == "list_directory":
                return await self._list_directory(tool_input["path"])
            elif tool_name == "run_command":
                return await self._run_command(tool_input["command"])
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            logger.error("Tool %s failed: %s", tool_name, e)
            return f"Error: {e}"

    async def _read_file(self, path: str) -> str:
        # Try workspace first, then seed app
        try:
            return self.workspace.read_file(path)
        except FileNotFoundError:
            pass

        seed_path = self.seed_app_path / path
        if seed_path.exists() and seed_path.is_file():
            return seed_path.read_text()

        return f"Error: File not found: {path}"

    async def _write_file(self, path: str, content: str, agent: str, event_bus: EventBus) -> str:
        full_path = self.workspace.write_file(path, content)
        lines = len(content.splitlines())
        await event_bus.emit(PipelineEvent(
            type=EventType.FILE_WRITE,
            agent=agent,
            data={"path": path, "lines": lines},
        ))
        return f"File written: {path} ({lines} lines)"

    async def _edit_file(self, path: str, old_string: str, new_string: str, agent: str, event_bus: EventBus) -> str:
        # Read from workspace or seed app
        try:
            content = self.workspace.read_file(path)
        except FileNotFoundError:
            seed_path = self.seed_app_path / path
            if seed_path.exists():
                content = seed_path.read_text()
            else:
                return f"Error: File not found: {path}"

        if old_string not in content:
            return f"Error: old_string not found in {path}"

        new_content = content.replace(old_string, new_string, 1)
        self.workspace.write_file(path, new_content)
        lines = len(new_content.splitlines())
        await event_bus.emit(PipelineEvent(
            type=EventType.FILE_WRITE,
            agent=agent,
            data={"path": path, "lines": lines},
        ))
        return f"File edited: {path}"

    async def _list_directory(self, path: str) -> str:
        # List from workspace, then seed app
        workspace_files = self.workspace.list_files(path)
        seed_dir = self.seed_app_path / path
        seed_files = []
        if seed_dir.exists() and seed_dir.is_dir():
            for p in sorted(seed_dir.rglob("*")):
                if p.is_file() and "__pycache__" not in str(p) and "node_modules" not in str(p) and ".venv" not in str(p):
                    seed_files.append(str(p.relative_to(self.seed_app_path)))

        all_files = sorted(set(workspace_files + seed_files))
        if not all_files:
            return "Directory is empty or does not exist"
        return "\n".join(all_files)

    async def _run_command(self, command: str) -> str:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(self.workspace.root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = stdout.decode() + stderr.decode()
            return output[:5000] if output else "(no output)"
        except asyncio.TimeoutError:
            return "Error: Command timed out after 30 seconds"
        except Exception as e:
            return f"Error: {e}"
