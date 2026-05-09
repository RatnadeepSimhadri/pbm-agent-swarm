"""Builds context messages for each agent — seed app files + prior agent outputs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.models import AgentRole, PipelineState

logger = logging.getLogger(__name__)

# Seed app files to inject per agent role (relative to seed-app/)
SEED_CONTEXT = {
    AgentRole.PRODUCT_MANAGER: [
        "README.md",
    ],
    AgentRole.TECH_LEAD: [],
    AgentRole.ARCHITECT: [
        "README.md",
        "backend/app/models/drug.py",
        "backend/app/models/formulary.py",
        "backend/app/models/member.py",
        "backend/app/routes/drugs.py",
        "backend/app/services/drug_service.py",
        "backend/app/schemas/drug.py",
        "backend/app/main.py",
        "frontend/src/App.jsx",
        "frontend/src/components/Sidebar.jsx",
    ],
    AgentRole.BACKEND_DEV: [
        "README.md",
        "backend/app/database.py",
        "backend/app/auth.py",
        "backend/app/models/drug.py",
        "backend/app/models/formulary.py",
        "backend/app/models/member.py",
        "backend/app/models/plan.py",
        "backend/app/routes/drugs.py",
        "backend/app/services/drug_service.py",
        "backend/app/services/formulary_service.py",
        "backend/app/schemas/drug.py",
        "backend/app/schemas/formulary.py",
        "backend/app/main.py",
    ],
    AgentRole.FRONTEND_DEV: [
        "README.md",
        "frontend/src/pages/MedicationsPage.jsx",
        "frontend/src/hooks/useApi.js",
        "frontend/src/App.jsx",
        "frontend/src/components/Sidebar.jsx",
        "frontend/src/index.css",
    ],
    AgentRole.QA_ENGINEER: [
        "README.md",
    ],
}

# Which prior task outputs to inject per agent role
PRIOR_OUTPUTS = {
    AgentRole.PRODUCT_MANAGER: [],
    AgentRole.TECH_LEAD: ["pm"],
    AgentRole.ARCHITECT: ["pm", "tech_lead"],
    AgentRole.BACKEND_DEV: ["architect"],
    AgentRole.FRONTEND_DEV: ["architect"],
    AgentRole.QA_ENGINEER: ["architect", "backend_dev", "frontend_dev"],
}

TASK_DISPLAY = {
    "pm": "Product Manager's PRD",
    "tech_lead": "Tech Lead's Task Plan",
    "architect": "Architect's Specification",
    "backend_dev": "Backend Developer's Implementation",
    "frontend_dev": "Frontend Developer's Implementation",
    "qa": "QA Engineer's Test Report",
}


def build_context_messages(
    agent_role: AgentRole,
    pipeline: PipelineState,
    seed_app_path: str,
) -> list[dict[str, Any]]:
    """Build the context messages to inject before the task instruction."""
    messages = []
    seed_root = Path(seed_app_path).resolve()

    # 1. Inject seed app files
    seed_files = SEED_CONTEXT.get(agent_role, [])
    if seed_files:
        file_contents = []
        for rel_path in seed_files:
            full_path = seed_root / rel_path
            if full_path.exists():
                content = full_path.read_text()
                file_contents.append(f"### File: `{rel_path}`\n```\n{content}\n```")
            else:
                logger.warning("Seed file not found: %s", full_path)

        if file_contents:
            messages.append({
                "role": "user",
                "content": "Here are relevant files from the existing codebase. Study these patterns carefully — your output must be consistent with them.\n\n" + "\n\n".join(file_contents),
            })

    # 2. Inject prior agent outputs
    prior_task_ids = PRIOR_OUTPUTS.get(agent_role, [])
    for task_id in prior_task_ids:
        task = pipeline.get_task(task_id)
        if task and task.output:
            label = TASK_DISPLAY.get(task_id, task_id)
            messages.append({
                "role": "user",
                "content": f"Here is the {label}:\n\n{task.output}",
            })

        # For QA: also list artifacts written by prior agents
        if agent_role == AgentRole.QA_ENGINEER and task and task.artifacts:
            messages.append({
                "role": "user",
                "content": f"Files written by {label}:\n" + "\n".join(f"- `{a}`" for a in task.artifacts),
            })

    return messages
