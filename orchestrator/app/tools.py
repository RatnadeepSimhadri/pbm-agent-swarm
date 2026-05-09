"""Agent tool definitions for Anthropic API tool_use.

These are the tool schemas passed to Claude. In Phase 2, the mock runner
simulates tool calls. In Phase 4, these become real tool implementations.
"""

from __future__ import annotations

from typing import Any

# Tool definitions in Anthropic API format
FILESYSTEM_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file at the given path, relative to the workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to read",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file at the given path, relative to the workspace root. Creates parent directories as needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace a specific string in a file with new content. The old_string must match exactly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to edit",
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact string to find and replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "The replacement string",
                },
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "list_directory",
        "description": "List all files and directories at the given path, relative to the workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative directory path to list (use '' for root)",
                },
            },
            "required": ["path"],
        },
    },
]

COMMAND_TOOL = {
    "name": "run_command",
    "description": "Run a shell command in the workspace directory. Use for running tests, installing dependencies, or verifying code.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute",
            },
        },
        "required": ["command"],
    },
}


def get_tools_for_agent(agent_role: str) -> list[dict[str, Any]]:
    """Return the tool set appropriate for each agent role."""
    # PM and Tech Lead only read files
    if agent_role in ("product_manager", "tech_lead"):
        return [FILESYSTEM_TOOLS[0], FILESYSTEM_TOOLS[3]]  # read_file, list_directory

    # Architect reads and lists
    if agent_role == "architect":
        return [FILESYSTEM_TOOLS[0], FILESYSTEM_TOOLS[3]]

    # Backend Dev gets all filesystem tools + run_command
    if agent_role == "backend_dev":
        return FILESYSTEM_TOOLS + [COMMAND_TOOL]

    # Frontend Dev gets all filesystem tools
    if agent_role == "frontend_dev":
        return list(FILESYSTEM_TOOLS)

    # QA gets read, write, and run_command
    if agent_role == "qa_engineer":
        return [FILESYSTEM_TOOLS[0], FILESYSTEM_TOOLS[1], FILESYSTEM_TOOLS[3], COMMAND_TOOL]

    return list(FILESYSTEM_TOOLS)
