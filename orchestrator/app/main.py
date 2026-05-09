import asyncio
import logging
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.mock_runner import MockAgentRunner
from app.dag import DAGExecutor, build_pipeline
from app.events import EventBus
from app.models import PipelineState
from app.workspace import Workspace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PBM Agent Orchestrator",
    description="Multi-agent pipeline that takes business intent and produces working code.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
event_bus = EventBus()
current_pipeline: PipelineState | None = None
current_workspace: Workspace | None = None
pipeline_lock = asyncio.Lock()


class RunRequest(BaseModel):
    intent: str


class RunResponse(BaseModel):
    pipeline_id: str
    status: str
    message: str


@app.post("/api/run", response_model=RunResponse)
async def start_pipeline(request: RunRequest):
    global current_pipeline, current_workspace

    async with pipeline_lock:
        if current_pipeline and current_pipeline.status == "running":
            return RunResponse(
                pipeline_id=current_pipeline.id,
                status="already_running",
                message="A pipeline is already running",
            )

        # Set up workspace and pipeline
        pipeline_id = uuid.uuid4().hex[:12]
        current_workspace = Workspace(pipeline_id)
        current_pipeline = build_pipeline(
            intent=request.intent,
            pipeline_id=pipeline_id,
            workspace_path=str(current_workspace.root),
        )
        event_bus.clear_history()

    # Run pipeline in background
    asyncio.create_task(_run_pipeline())

    return RunResponse(
        pipeline_id=pipeline_id,
        status="started",
        message="Pipeline started",
    )


async def _run_pipeline():
    global current_pipeline
    runner = MockAgentRunner(current_workspace)
    executor = DAGExecutor(event_bus, runner)
    current_pipeline = await executor.execute(current_pipeline)


@app.get("/api/status")
async def get_status():
    if not current_pipeline:
        return {"status": "idle", "pipeline": None}
    return {
        "status": current_pipeline.status,
        "pipeline": {
            "id": current_pipeline.id,
            "intent": current_pipeline.intent,
            "status": current_pipeline.status,
            "tasks_completed": current_pipeline.tasks_completed,
            "tasks_total": current_pipeline.tasks_total,
            "elapsed": current_pipeline.elapsed,
            "total_tokens": current_pipeline.total_tokens,
            "total_lines": current_pipeline.total_lines,
            "tasks": [
                {
                    "id": t.id,
                    "agent": t.agent.value,
                    "display_name": t.display_name,
                    "status": t.status.value,
                    "duration": t.duration,
                    "tokens_used": t.tokens_used,
                }
                for t in current_pipeline.tasks
            ],
        },
    }


@app.get("/api/artifacts")
async def list_artifacts():
    if not current_workspace:
        return {"files": []}
    return {"files": current_workspace.list_files()}


@app.get("/api/artifacts/{path:path}")
async def get_artifact(path: str):
    if not current_workspace:
        return {"error": "No workspace active"}
    try:
        content = current_workspace.read_file(path)
        return {"path": path, "content": content}
    except FileNotFoundError:
        return {"error": f"File not found: {path}"}


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "orchestrator",
        "ws_clients": event_bus.client_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await event_bus.connect(ws)
    try:
        while True:
            # Keep connection alive, listen for client messages (unused for now)
            await ws.receive_text()
    except WebSocketDisconnect:
        await event_bus.disconnect(ws)
