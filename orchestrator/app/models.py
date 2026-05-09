from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class AgentRole(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    TECH_LEAD = "tech_lead"
    ARCHITECT = "architect"
    BACKEND_DEV = "backend_dev"
    FRONTEND_DEV = "frontend_dev"
    QA_ENGINEER = "qa_engineer"


AGENT_DISPLAY_NAMES = {
    AgentRole.PRODUCT_MANAGER: "Product Manager",
    AgentRole.TECH_LEAD: "Tech Lead",
    AgentRole.ARCHITECT: "Architect",
    AgentRole.BACKEND_DEV: "Backend Dev",
    AgentRole.FRONTEND_DEV: "Frontend Dev",
    AgentRole.QA_ENGINEER: "QA Engineer",
}


class PipelineTask(BaseModel):
    id: str
    agent: AgentRole
    display_name: str = ""
    status: TaskStatus = TaskStatus.QUEUED
    dependencies: list[str] = Field(default_factory=list)
    output: str = ""
    artifacts: list[str] = Field(default_factory=list)
    tokens_used: int = 0
    started_at: float | None = None
    completed_at: float | None = None
    error: str | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.display_name:
            self.display_name = AGENT_DISPLAY_NAMES.get(self.agent, self.id)

    @property
    def duration(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at


class PipelineState(BaseModel):
    id: str
    intent: str
    tasks: list[PipelineTask]
    status: str = "pending"  # pending, running, completed, failed
    started_at: float | None = None
    completed_at: float | None = None
    workspace_path: str = ""
    total_tokens: int = 0
    total_lines: int = 0

    def get_task(self, task_id: str) -> PipelineTask | None:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    @property
    def tasks_completed(self) -> int:
        return sum(1 for t in self.tasks if t.status == TaskStatus.DONE)

    @property
    def tasks_total(self) -> int:
        return len(self.tasks)

    @property
    def elapsed(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at


class EventType(str, Enum):
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    TASK_STATE_CHANGE = "task_state_change"
    AGENT_OUTPUT = "agent_output"
    TOOL_CALL = "tool_call"
    FILE_WRITE = "file_write"
    TEST_RESULT = "test_result"
    METRICS_UPDATE = "metrics_update"
    ERROR = "error"


class PipelineEvent(BaseModel):
    type: EventType
    agent: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
