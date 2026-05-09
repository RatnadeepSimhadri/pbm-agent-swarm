"""Agent runner interface. Phase 2 uses MockAgentRunner, Phase 4 swaps in real Claude calls."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.events import EventBus
    from app.models import PipelineState, PipelineTask


class AgentRunner(ABC):
    @abstractmethod
    async def run(
        self,
        pipeline: PipelineState,
        task: PipelineTask,
        event_bus: EventBus,
    ) -> dict[str, Any]:
        """Run an agent and return result dict with keys: output, artifacts, tokens_used, lines_written."""
        ...
