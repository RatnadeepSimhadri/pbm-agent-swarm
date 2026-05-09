from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from app.models import (
    AgentRole,
    EventType,
    PipelineEvent,
    PipelineState,
    PipelineTask,
    TaskStatus,
)

if TYPE_CHECKING:
    from app.events import EventBus
    from app.agents.runner import AgentRunner

logger = logging.getLogger(__name__)


def build_pipeline(intent: str, pipeline_id: str, workspace_path: str) -> PipelineState:
    """Build the 6-agent DAG with dependency edges.

    Pipeline topology:
        PM → Tech Lead → Architect → [Backend Dev, Frontend Dev] → QA
    """
    tasks = [
        PipelineTask(
            id="pm",
            agent=AgentRole.PRODUCT_MANAGER,
            dependencies=[],
        ),
        PipelineTask(
            id="tech_lead",
            agent=AgentRole.TECH_LEAD,
            dependencies=["pm"],
        ),
        PipelineTask(
            id="architect",
            agent=AgentRole.ARCHITECT,
            dependencies=["tech_lead"],
        ),
        PipelineTask(
            id="backend_dev",
            agent=AgentRole.BACKEND_DEV,
            dependencies=["architect"],
        ),
        PipelineTask(
            id="frontend_dev",
            agent=AgentRole.FRONTEND_DEV,
            dependencies=["architect"],
        ),
        PipelineTask(
            id="qa",
            agent=AgentRole.QA_ENGINEER,
            dependencies=["backend_dev", "frontend_dev"],
        ),
    ]

    return PipelineState(
        id=pipeline_id,
        intent=intent,
        tasks=tasks,
        workspace_path=workspace_path,
    )


class DAGExecutor:
    """Async DAG executor that runs tasks when dependencies are satisfied."""

    def __init__(self, event_bus: EventBus, agent_runner: AgentRunner):
        self.event_bus = event_bus
        self.agent_runner = agent_runner
        self._running_tasks: dict[str, asyncio.Task] = {}

    async def execute(self, pipeline: PipelineState) -> PipelineState:
        pipeline.status = "running"
        pipeline.started_at = time.time()

        await self.event_bus.emit(PipelineEvent(
            type=EventType.PIPELINE_START,
            data={
                "pipeline_id": pipeline.id,
                "intent": pipeline.intent,
                "tasks": [t.model_dump() for t in pipeline.tasks],
            },
        ))

        try:
            await self._run_dag(pipeline)

            all_done = all(t.status == TaskStatus.DONE for t in pipeline.tasks)
            pipeline.status = "completed" if all_done else "failed"
        except Exception as e:
            logger.exception("Pipeline execution failed")
            pipeline.status = "failed"
            await self.event_bus.emit(PipelineEvent(
                type=EventType.ERROR,
                data={"error": str(e)},
            ))

        pipeline.completed_at = time.time()
        pipeline.total_tokens = sum(t.tokens_used for t in pipeline.tasks)

        await self.event_bus.emit(PipelineEvent(
            type=EventType.PIPELINE_COMPLETE,
            data={
                "pipeline_id": pipeline.id,
                "status": pipeline.status,
                "elapsed": pipeline.elapsed,
                "tasks_completed": pipeline.tasks_completed,
                "tasks_total": pipeline.tasks_total,
                "total_tokens": pipeline.total_tokens,
            },
        ))

        return pipeline

    async def _run_dag(self, pipeline: PipelineState) -> None:
        """Poll for ready tasks and launch them until all are done or failed."""
        while True:
            # Find tasks that are ready to run (all deps satisfied)
            ready = self._get_ready_tasks(pipeline)

            if not ready and not self._running_tasks:
                # Nothing ready and nothing running — we're done
                break

            # Launch ready tasks concurrently
            for task in ready:
                logger.info("Launching task: %s (%s)", task.id, task.display_name)
                task.status = TaskStatus.ASSIGNED
                await self._emit_state_change(task)
                async_task = asyncio.create_task(self._run_task(pipeline, task))
                self._running_tasks[task.id] = async_task

            # Wait for at least one running task to complete
            if self._running_tasks:
                done, _ = await asyncio.wait(
                    self._running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                # Clean up completed tasks
                for completed in done:
                    task_id = next(
                        tid for tid, t in self._running_tasks.items()
                        if t is completed
                    )
                    del self._running_tasks[task_id]
                    # Re-raise if the task raised an exception
                    if completed.exception():
                        logger.error(
                            "Task %s raised: %s", task_id, completed.exception()
                        )

    def _get_ready_tasks(self, pipeline: PipelineState) -> list[PipelineTask]:
        """Return tasks whose dependencies are all DONE and that are still QUEUED."""
        ready = []
        for task in pipeline.tasks:
            if task.status != TaskStatus.QUEUED:
                continue
            deps_satisfied = all(
                pipeline.get_task(dep_id).status == TaskStatus.DONE
                for dep_id in task.dependencies
            )
            if deps_satisfied:
                ready.append(task)
        return ready

    async def _run_task(self, pipeline: PipelineState, task: PipelineTask) -> None:
        """Run a single agent task."""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = time.time()
        await self._emit_state_change(task)

        try:
            result = await self.agent_runner.run(pipeline, task, self.event_bus)
            task.output = result.get("output", "")
            task.artifacts = result.get("artifacts", [])
            task.tokens_used = result.get("tokens_used", 0)
            task.status = TaskStatus.DONE

            # Update pipeline-level metrics
            pipeline.total_lines += result.get("lines_written", 0)

        except Exception as e:
            logger.exception("Task %s failed", task.id)
            task.status = TaskStatus.FAILED
            task.error = str(e)

        task.completed_at = time.time()
        await self._emit_state_change(task)

    async def _emit_state_change(self, task: PipelineTask) -> None:
        await self.event_bus.emit(PipelineEvent(
            type=EventType.TASK_STATE_CHANGE,
            agent=task.agent.value,
            data={
                "task_id": task.id,
                "status": task.status.value,
                "display_name": task.display_name,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error": task.error,
            },
        ))
