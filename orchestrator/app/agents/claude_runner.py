"""Real agent runner using Anthropic Claude API with streaming."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import anthropic

from app.agents.context import build_context_messages
from app.agents.runner import AgentRunner
from app.agents.tool_executor import ToolExecutor
from app.config import settings
from app.events import EventBus
from app.models import AgentRole, EventType, PipelineEvent, PipelineState, PipelineTask
from app.tools import get_tools_for_agent
from app.workspace import Workspace

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_prompt(agent_role: str) -> str:
    prompt_file = PROMPTS_DIR / f"{agent_role}.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text()


class ClaudeAgentRunner(AgentRunner):
    def __init__(self, workspace: Workspace, seed_app_path: str, deploy_runner=None):
        self.workspace = workspace
        self.seed_app_path = seed_app_path
        self.deploy_runner = deploy_runner
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.tool_executor = ToolExecutor(workspace, seed_app_path)

    async def run(
        self,
        pipeline: PipelineState,
        task: PipelineTask,
        event_bus: EventBus,
    ) -> dict[str, Any]:
        # Deployer is handled by the shared DeployRunner
        if task.agent == AgentRole.DEPLOYER and self.deploy_runner:
            return await self.deploy_runner.run(pipeline, task, event_bus)

        agent_role = task.agent.value
        agent_name = agent_role

        # Load system prompt
        system_prompt = _load_prompt(agent_role)

        # Build context messages (seed files + prior outputs)
        context_messages = build_context_messages(
            task.agent, pipeline, self.seed_app_path,
        )

        # Add the task instruction
        task_instruction = self._build_task_instruction(pipeline, task)
        context_messages.append({
            "role": "user",
            "content": task_instruction,
        })

        # Get tools for this agent
        tools = get_tools_for_agent(agent_role)

        # Run the agent loop (may require multiple rounds for tool use)
        messages = list(context_messages)
        total_input_tokens = 0
        total_output_tokens = 0
        full_output = ""
        artifacts = []

        while True:
            # Call Claude with streaming
            text_output, tool_calls, input_tokens, output_tokens = await self._stream_call(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools,
                agent_name=agent_name,
                event_bus=event_bus,
            )

            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            full_output += text_output

            # If no tool calls, we're done
            if not tool_calls:
                break

            # Execute tool calls and build the next messages
            assistant_content = []
            if text_output:
                assistant_content.append({"type": "text", "text": text_output})
            for tc in tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["input"],
                })

            messages.append({"role": "assistant", "content": assistant_content})

            # Execute each tool and collect results
            tool_results = []
            for tc in tool_calls:
                result = await self.tool_executor.execute(
                    tc["name"], tc["input"], agent_name, event_bus,
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result,
                })

                # Track artifacts from write_file calls
                if tc["name"] == "write_file":
                    path = tc["input"].get("path", "")
                    if path and path not in artifacts:
                        artifacts.append(path)
                elif tc["name"] == "edit_file":
                    path = tc["input"].get("path", "")
                    if path and path not in artifacts:
                        artifacts.append(path)

            messages.append({"role": "user", "content": tool_results})

        # Calculate lines written
        lines_written = self.workspace.count_lines()

        return {
            "output": full_output,
            "artifacts": artifacts,
            "tokens_used": total_input_tokens + total_output_tokens,
            "lines_written": lines_written,
        }

    async def _stream_call(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict],
        agent_name: str,
        event_bus: EventBus,
    ) -> tuple[str, list[dict], int, int]:
        """Make a streaming API call. Returns (text_output, tool_calls, input_tokens, output_tokens)."""
        text_output = ""
        tool_calls = []
        current_tool: dict | None = None
        current_tool_json = ""

        kwargs: dict[str, Any] = {
            "model": settings.model,
            "max_tokens": 8192,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        with self.client.messages.stream(**kwargs) as stream:
            for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        current_tool = {
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "input": {},
                        }
                        current_tool_json = ""

                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        text = event.delta.text
                        text_output += text
                        await event_bus.emit(PipelineEvent(
                            type=EventType.AGENT_OUTPUT,
                            agent=agent_name,
                            data={"content": text, "done": False},
                        ))
                    elif event.delta.type == "input_json_delta":
                        if current_tool is not None:
                            current_tool_json += event.delta.partial_json

                elif event.type == "content_block_stop":
                    if current_tool is not None:
                        import json
                        try:
                            current_tool["input"] = json.loads(current_tool_json) if current_tool_json else {}
                        except json.JSONDecodeError:
                            current_tool["input"] = {}
                        tool_calls.append(current_tool)
                        current_tool = None
                        current_tool_json = ""

            # Get usage from the final message
            final = stream.get_final_message()
            input_tokens = final.usage.input_tokens
            output_tokens = final.usage.output_tokens

        # Signal output done for this round
        await event_bus.emit(PipelineEvent(
            type=EventType.AGENT_OUTPUT,
            agent=agent_name,
            data={"content": "", "done": True},
        ))

        return text_output, tool_calls, input_tokens, output_tokens

    def _build_task_instruction(self, pipeline: PipelineState, task: PipelineTask) -> str:
        """Build the final user message with the task instruction."""
        intent = pipeline.intent

        instructions = {
            "product_manager": f"Write a PRD for the following feature request:\n\n> {intent}",
            "tech_lead": f"Break down the above PRD into an engineering task plan with dependencies.\n\nOriginal intent: {intent}",
            "architect": f"Design the architecture specification for implementing the above PRD and task plan.\n\nUse the `read_file` and `list_directory` tools to examine the existing codebase before designing.\n\nOriginal intent: {intent}",
            "backend_dev": f"Implement the backend code according to the architecture specification above.\n\nUse `read_file` to examine existing patterns first, then use `write_file` to create new files and `edit_file` to modify existing ones.\n\nWrite all files relative to the workspace root (backend/ prefix for backend files).\n\nOriginal intent: {intent}",
            "frontend_dev": f"Implement the frontend code according to the architecture specification above.\n\nUse `read_file` to examine existing patterns first, then use `write_file` to create new files and `edit_file` to modify existing ones.\n\nWrite all files relative to the workspace root (frontend/ prefix for frontend files).\n\nOriginal intent: {intent}",
            "qa_engineer": f"Write and run integration tests for the feature described above.\n\nUse `read_file` to examine the new code, then `write_file` to create test files, and `run_command` to run pytest.\n\nWrite test files relative to the workspace root (backend/tests/ prefix).\n\nOriginal intent: {intent}",
        }

        return instructions.get(task.agent.value, f"Complete your task for: {intent}")
