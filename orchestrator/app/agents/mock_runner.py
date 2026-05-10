"""Mock agent runner that simulates all 7 agents with canned output and realistic delays."""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any

from app.agents.runner import AgentRunner
from app.events import EventBus
from app.models import AgentRole, EventType, PipelineEvent, PipelineState, PipelineTask
from app.workspace import Workspace

# Simulated token streaming speed — tuned to look like real Claude output
# ~10 events/sec per agent, readable pace for a demo
CHARS_PER_CHUNK = 60
CHUNK_DELAY = 0.08  # 80ms between chunks

# Keywords that trigger the chat bubble scenario instead of drug cost checker
CHAT_KEYWORDS = ["chat", "bubble", "ask questions", "conversational", "assistant"]


async def _stream_text(
    text: str, agent: str, event_bus: EventBus, event_type: EventType = EventType.AGENT_OUTPUT
) -> None:
    """Simulate streaming by emitting text in small chunks."""
    for i in range(0, len(text), CHARS_PER_CHUNK):
        chunk = text[i:i + CHARS_PER_CHUNK]
        await event_bus.emit(PipelineEvent(
            type=event_type,
            agent=agent,
            data={"content": chunk, "done": i + CHARS_PER_CHUNK >= len(text)},
        ))
        await asyncio.sleep(CHUNK_DELAY)


async def _emit_tool_call(agent: str, tool: str, args: dict, event_bus: EventBus) -> None:
    await event_bus.emit(PipelineEvent(
        type=EventType.TOOL_CALL,
        agent=agent,
        data={"tool": tool, "arguments": args},
    ))
    await asyncio.sleep(0.2)


async def _emit_file_write(agent: str, path: str, lines: int, event_bus: EventBus) -> None:
    await event_bus.emit(PipelineEvent(
        type=EventType.FILE_WRITE,
        agent=agent,
        data={"path": path, "lines": lines},
    ))


class MockAgentRunner(AgentRunner):
    def __init__(self, workspace: Workspace, deploy_runner=None, seed_app_path: str = "../seed-app"):
        self.workspace = workspace
        self.deploy_runner = deploy_runner
        self.seed_app_path = os.path.abspath(seed_app_path)

    def _patch_backend_main(self, module_name: str) -> str:
        """Read seed-app main.py and add a route module idempotently."""
        main_py = Path(self.seed_app_path, "backend/app/main.py").read_text()

        # Add to import line if not already present
        match = re.search(r"from app\.routes import (.+)", main_py)
        if match:
            modules = [m.strip() for m in match.group(1).split(",")]
            if module_name not in modules:
                modules.append(module_name)
                modules.sort()
                new_import = "from app.routes import " + ", ".join(modules)
                main_py = main_py.replace(match.group(0), new_import)

        # Add router registration if not already present
        router_line = f"app.include_router({module_name}.router)"
        if router_line not in main_py:
            main_py = main_py.replace(
                "app.include_router(formulary.router)",
                f"app.include_router(formulary.router)\napp.include_router({module_name}.router)",
            )

        return main_py

    def _detect_scenario(self, intent: str) -> str:
        lower = intent.lower()
        for kw in CHAT_KEYWORDS:
            if kw in lower:
                return "chat_bubble"
        return "drug_cost_checker"

    async def run(
        self,
        pipeline: PipelineState,
        task: PipelineTask,
        event_bus: EventBus,
    ) -> dict[str, Any]:
        # Deployer is handled by the shared DeployRunner
        if task.agent == AgentRole.DEPLOYER and self.deploy_runner:
            return await self.deploy_runner.run(pipeline, task, event_bus)

        self._scenario = self._detect_scenario(pipeline.intent)

        agent = task.agent.value
        handlers = {
            AgentRole.PRODUCT_MANAGER: self._run_pm,
            AgentRole.TECH_LEAD: self._run_tech_lead,
            AgentRole.ARCHITECT: self._run_architect,
            AgentRole.BACKEND_DEV: self._run_backend_dev,
            AgentRole.FRONTEND_DEV: self._run_frontend_dev,
            AgentRole.QA_ENGINEER: self._run_qa,
        }
        handler = handlers[task.agent]
        return await handler(pipeline, task, event_bus)

    async def _run_pm(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        if self._scenario == "chat_bubble":
            return await self._run_pm_chat(pipeline, task, event_bus)
        agent = task.agent.value
        prd = f"""# Product Requirements Document

## Feature: Drug Cost Checker

### Problem Statement
Members currently have no way to check what their medications will cost before filling a prescription. This leads to surprise costs at the pharmacy counter, medication non-adherence due to cost concerns, and increased call center volume for cost inquiries.

### Intent
> {pipeline.intent}

### Target Personas
1. **Active Member** — Regularly fills prescriptions, wants to budget for medication costs
2. **New Member** — Recently enrolled, exploring their coverage and formulary
3. **Caregiver** — Managing medications for a family member, needs cost transparency

### User Stories
1. As a member, I want to search for a medication and see my estimated copay so I can budget accordingly
2. As a member, I want to see tier information for a drug so I understand why my costs vary
3. As a member, I want to compare generic vs. brand costs so I can make informed choices
4. As a member, I want to see if prior authorization is required before my doctor submits the prescription

### Acceptance Criteria
- **AC1**: Member can search for a drug by name and see their copay based on their plan's formulary
- **AC2**: Results show tier level, copay amount, and coverage details (prior auth, step therapy, quantity limits)
- **AC3**: Drug search supports partial matching and shows both generic and brand options
- **AC4**: Cost checker page is accessible from the main navigation
- **AC5**: The feature works for all three plan types (Gold, Silver, Bronze) with correct copay amounts

### Non-Functional Requirements
- Response time: cost lookup < 500ms
- Accessible: WCAG 2.1 AA compliant
- Mobile-responsive layout

### Out of Scope
- Real-time pharmacy pricing (different from copay)
- Mail-order vs. retail price comparison
- Prior authorization submission workflow
"""

        await _stream_text(prd, agent, event_bus)

        # Write PRD artifact
        self.workspace.write_file("prd.md", prd)
        await _emit_file_write(agent, "prd.md", len(prd.splitlines()), event_bus)

        return {
            "output": prd,
            "artifacts": ["prd.md"],
            "tokens_used": 1847,
            "lines_written": len(prd.splitlines()),
        }

    async def _run_tech_lead(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        if self._scenario == "chat_bubble":
            return await self._run_tech_lead_chat(pipeline, task, event_bus)
        agent = task.agent.value
        task_plan = """# Task Breakdown & Dependency Graph

## Tasks

### T1: API Endpoint — Drug Cost Lookup
- **Assignee**: Backend Dev
- **AC**: AC1, AC2, AC3
- **Description**: Create `GET /api/cost-estimate` endpoint that accepts drug search query and member's plan, returns copay/tier info
- **Dependencies**: None (uses existing models)

### T2: Cost Estimation Service
- **Assignee**: Backend Dev
- **AC**: AC1, AC5
- **Description**: Business logic to look up drug in member's formulary, return tier + copay for their plan
- **Dependencies**: T1

### T3: Frontend — Cost Checker Page
- **Assignee**: Frontend Dev
- **AC**: AC1, AC3, AC4
- **Description**: New page with drug search input, results display showing copay/tier/coverage
- **Dependencies**: T1 (needs API contract)

### T4: Navigation Integration
- **Assignee**: Frontend Dev
- **AC**: AC4
- **Description**: Add "Cost Checker" to sidebar navigation and route
- **Dependencies**: T3

### T5: Integration Tests
- **Assignee**: QA Engineer
- **AC**: AC1-AC5
- **Description**: pytest tests covering cost lookup across all plans, search, edge cases
- **Dependencies**: T1, T2

## Dependency DAG
```mermaid
graph LR
    T1[T1: API Endpoint] --> T2[T2: Cost Service]
    T1 --> T3[T3: Cost Checker Page]
    T3 --> T4[T4: Navigation]
    T1 --> T5[T5: Integration Tests]
    T2 --> T5
```

## Parallelism
- T3/T4 (Frontend) and T1/T2 (Backend) can proceed in parallel after architect spec
- T5 (Tests) runs after backend is complete
"""

        await _stream_text(task_plan, agent, event_bus)

        self.workspace.write_file("task_plan.md", task_plan)
        await _emit_file_write(agent, "task_plan.md", len(task_plan.splitlines()), event_bus)

        return {
            "output": task_plan,
            "artifacts": ["task_plan.md"],
            "tokens_used": 1203,
            "lines_written": len(task_plan.splitlines()),
        }

    async def _run_architect(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        if self._scenario == "chat_bubble":
            return await self._run_architect_chat(pipeline, task, event_bus)
        agent = task.agent.value

        # Simulate reading seed app files
        await _emit_tool_call(agent, "list_directory", {"path": ""}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "backend/app/routes/drugs.py"}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "backend/app/services/formulary_service.py"}, event_bus)

        spec = """# Architecture Specification — Drug Cost Checker

## API Contract

### `GET /api/cost-estimate`

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| drug_name | string | yes | Full or partial drug name to search |

**Response** `200 OK`:
```json
{
  "results": [
    {
      "drug_id": 1,
      "drug_name": "Metformin",
      "generic_name": "metformin",
      "brand_name": null,
      "strength": "500mg",
      "form": "tablet",
      "tier": 1,
      "tier_name": "Preferred Generic",
      "copay_amount": 10.00,
      "prior_auth_required": false,
      "step_therapy_required": false,
      "quantity_limit": 30
    }
  ],
  "member_plan": "Gold Plan",
  "total_results": 1
}
```

## Data Model Changes
None — the existing `FormularyDrug` model already contains all required data (tier, copay, prior_auth, step_therapy, quantity_limit). We join through `Member → Plan → Formulary → FormularyDrug → Drug`.

## Backend Components
1. **Route**: `app/routes/cost_estimate.py` — new router, `GET /api/cost-estimate`
2. **Service**: `app/services/cost_estimate_service.py` — query logic joining member's formulary with drug search
3. **Schema**: `app/schemas/cost_estimate.py` — response models
4. **Registration**: Add router to `app/main.py`

## Frontend Components
1. **Page**: `src/pages/CostCheckerPage.jsx` — search input + results cards
2. **Route**: Add `/cost-checker` route in `App.jsx`
3. **Navigation**: Add "Cost Checker" item to `Sidebar.jsx` nav array

## Request Flow

```mermaid
sequenceDiagram
    participant U as Member UI
    participant FE as CostCheckerPage
    participant API as GET /api/cost-estimate
    participant SVC as cost_estimate_service
    participant DB as SQLite

    U->>FE: Enter drug name
    FE->>API: ?drug_name=metformin
    API->>SVC: estimate_cost(member_id, drug_name)
    SVC->>DB: JOIN Formulary + Drug + Plan
    DB-->>SVC: FormularyDrug rows
    SVC-->>API: {results, member_plan, total}
    API-->>FE: CostEstimateResponse
    FE-->>U: Render result cards
```

## Component Spec — CostCheckerPage

**Layout:**
- Page heading: "Drug Cost Checker" with subtitle
- Search bar: text input + "Check Cost" button
- Results grid: 2-column card layout

**Result Card Fields:**
- Drug name, strength, form
- Tier badge (color-coded: Tier 1 green, Tier 2 blue, Tier 3 amber, Tier 4 red)
- Copay amount (large, prominent)
- Prior authorization status
- Step therapy requirement
- Quantity limit per fill
"""

        await _stream_text(spec, agent, event_bus)

        self.workspace.write_file("architecture_spec.md", spec)
        await _emit_file_write(agent, "architecture_spec.md", len(spec.splitlines()), event_bus)

        return {
            "output": spec,
            "artifacts": ["architecture_spec.md"],
            "tokens_used": 2105,
            "lines_written": len(spec.splitlines()),
        }

    async def _run_backend_dev(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        if self._scenario == "chat_bubble":
            return await self._run_backend_dev_chat(pipeline, task, event_bus)
        agent = task.agent.value

        # Simulate reading existing patterns
        await _emit_tool_call(agent, "read_file", {"path": "backend/app/routes/drugs.py"}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "backend/app/services/drug_service.py"}, event_bus)

        # Schema
        schema_code = '''from pydantic import BaseModel, ConfigDict


class CostEstimateResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drug_id: int
    drug_name: str
    generic_name: str | None
    brand_name: str | None
    strength: str
    form: str
    tier: int
    tier_name: str
    copay_amount: float
    prior_auth_required: bool
    step_therapy_required: bool
    quantity_limit: int | None


class CostEstimateResponse(BaseModel):
    results: list[CostEstimateResult]
    member_plan: str
    total_results: int
'''
        await _stream_text("Creating schema: `app/schemas/cost_estimate.py`\n\n```python\n" + schema_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/app/schemas/cost_estimate.py", schema_code)
        await _emit_file_write(agent, "backend/app/schemas/cost_estimate.py", len(schema_code.splitlines()), event_bus)

        # Service
        service_code = '''from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.drug import Drug
from app.models.formulary import Formulary, FormularyDrug
from app.models.member import Member

TIER_NAMES = {
    1: "Preferred Generic",
    2: "Non-Preferred Generic",
    3: "Preferred Brand",
    4: "Specialty",
}


def estimate_cost(db: Session, member_id: int, drug_name: str) -> dict:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return {"results": [], "member_plan": "", "total_results": 0}

    plan = member.plan
    formulary = db.query(Formulary).filter(Formulary.plan_id == plan.id).first()
    if not formulary:
        return {"results": [], "member_plan": plan.name, "total_results": 0}

    search = f"%{drug_name}%"
    entries = (
        db.query(FormularyDrug)
        .join(Drug, FormularyDrug.drug_id == Drug.id)
        .filter(
            FormularyDrug.formulary_id == formulary.id,
            or_(
                Drug.name.ilike(search),
                Drug.generic_name.ilike(search),
                Drug.brand_name.ilike(search),
            ),
        )
        .options(joinedload(FormularyDrug.drug))
        .all()
    )

    results = []
    for entry in entries:
        results.append({
            "drug_id": entry.drug.id,
            "drug_name": entry.drug.name,
            "generic_name": entry.drug.generic_name,
            "brand_name": entry.drug.brand_name,
            "strength": entry.drug.strength,
            "form": entry.drug.form,
            "tier": entry.tier,
            "tier_name": TIER_NAMES.get(entry.tier, f"Tier {entry.tier}"),
            "copay_amount": entry.copay_amount,
            "prior_auth_required": entry.prior_auth_required,
            "step_therapy_required": entry.step_therapy_required,
            "quantity_limit": entry.quantity_limit,
        })

    return {
        "results": results,
        "member_plan": plan.name,
        "total_results": len(results),
    }
'''
        await _stream_text("\nCreating service: `app/services/cost_estimate_service.py`\n\n```python\n" + service_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/app/services/cost_estimate_service.py", service_code)
        await _emit_file_write(agent, "backend/app/services/cost_estimate_service.py", len(service_code.splitlines()), event_bus)

        # Route
        route_code = '''from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_member
from app.database import get_db
from app.models.member import Member
from app.schemas.cost_estimate import CostEstimateResponse
from app.services.cost_estimate_service import estimate_cost

router = APIRouter(prefix="/api/cost-estimate", tags=["cost-estimate"])


@router.get("", response_model=CostEstimateResponse)
def get_cost_estimate(
    drug_name: str = Query(..., description="Drug name to search"),
    db: Session = Depends(get_db),
    member: Member = Depends(get_current_member),
):
    result = estimate_cost(db, member.id, drug_name)
    return CostEstimateResponse(**result)
'''
        await _stream_text("\nCreating route: `app/routes/cost_estimate.py`\n\n```python\n" + route_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/app/routes/cost_estimate.py", route_code)
        await _emit_file_write(agent, "backend/app/routes/cost_estimate.py", len(route_code.splitlines()), event_bus)

        # Edit main.py to register the router (idempotent — safe to stack with other features)
        await _stream_text("\nRegistering router in `app/main.py`:\n```python\nfrom app.routes import cost_estimate\napp.include_router(cost_estimate.router)\n```\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "backend/app/main.py", "old_string": "from app.routes import auth, drugs, ...", "new_string": "from app.routes import auth, cost_estimate, drugs, ..."}, event_bus)

        main_py = self._patch_backend_main("cost_estimate")
        self.workspace.write_file("backend/app/main.py", main_py)
        await _emit_file_write(agent, "backend/app/main.py", len(main_py.splitlines()), event_bus)

        total_lines = len(schema_code.splitlines()) + len(service_code.splitlines()) + len(route_code.splitlines()) + len(main_py.splitlines())
        return {
            "output": "Backend implementation complete: schema, service, route for /api/cost-estimate",
            "artifacts": [
                "backend/app/schemas/cost_estimate.py",
                "backend/app/services/cost_estimate_service.py",
                "backend/app/routes/cost_estimate.py",
                "backend/app/main.py",
            ],
            "tokens_used": 3421,
            "lines_written": total_lines,
        }

    async def _run_frontend_dev(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        if self._scenario == "chat_bubble":
            return await self._run_frontend_dev_chat(pipeline, task, event_bus)
        agent = task.agent.value

        # Simulate reading existing patterns
        await _emit_tool_call(agent, "read_file", {"path": "frontend/src/pages/MedicationsPage.jsx"}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "frontend/src/components/Sidebar.jsx"}, event_bus)

        page_code = '''import { useCallback, useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';

const TIER_BADGES = {
  1: 'bg-emerald-100 text-emerald-800',
  2: 'bg-blue-100 text-blue-800',
  3: 'bg-amber-100 text-amber-800',
  4: 'bg-red-100 text-red-800',
};

export function CostCheckerPage() {
  const { get } = useApi();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [memberPlan, setMemberPlan] = useState('');

  const search = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await get(`/api/cost-estimate?drug_name=${encodeURIComponent(query)}`);
      setResults(data.results);
      setMemberPlan(data.member_plan);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [get, query]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Drug Cost Checker</h1>
        <p className="text-slate-500 mt-1">Estimate your copay before filling a prescription</p>
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="Enter medication name..."
          className="flex-1 max-w-md px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
        />
        <button
          onClick={search}
          disabled={loading || !query.trim()}
          className="px-6 py-2.5 bg-primary-700 text-white rounded-lg text-sm font-medium hover:bg-primary-800 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Check Cost'}
        </button>
      </div>

      {results && (
        <div>
          <p className="text-sm text-slate-500 mb-4">
            {results.length} result(s) for your {memberPlan}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((r) => (
              <div key={r.drug_id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">{r.drug_name}</h3>
                    <p className="text-xs text-slate-500">{r.strength} {r.form}</p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TIER_BADGES[r.tier]}`}>
                    {r.tier_name}
                  </span>
                </div>
                <div className="text-3xl font-bold text-primary-700 mb-3">${r.copay_amount.toFixed(2)}</div>
                <div className="space-y-1 text-xs text-slate-500">
                  {r.prior_auth_required && <p className="text-amber-600">Prior authorization required</p>}
                  {r.step_therapy_required && <p className="text-amber-600">Step therapy required</p>}
                  {r.quantity_limit && <p>Quantity limit: {r.quantity_limit} per fill</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
'''

        await _stream_text("Creating page: `src/pages/CostCheckerPage.jsx`\n\n```jsx\n" + page_code + "```\n", agent, event_bus)
        self.workspace.write_file("frontend/src/pages/CostCheckerPage.jsx", page_code)
        await _emit_file_write(agent, "frontend/src/pages/CostCheckerPage.jsx", len(page_code.splitlines()), event_bus)

        # Edit App.jsx to add route (idempotent)
        await _stream_text("\nAdding route to `App.jsx`...\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "frontend/src/App.jsx", "old_string": "import { MedicationsPage }...", "new_string": "import { CostCheckerPage }..."}, event_bus)

        app_jsx = Path(self.seed_app_path, "frontend/src/App.jsx").read_text()
        if "CostCheckerPage" not in app_jsx:
            app_jsx = app_jsx.replace(
                "import { MedicationsPage } from './pages/MedicationsPage';",
                "import { MedicationsPage } from './pages/MedicationsPage';\nimport { CostCheckerPage } from './pages/CostCheckerPage';",
            )
            app_jsx = app_jsx.replace(
                '<Route path="/medications" element={<MedicationsPage />} />',
                '<Route path="/medications" element={<MedicationsPage />} />\n            <Route path="/cost-checker" element={<CostCheckerPage />} />',
            )
        self.workspace.write_file("frontend/src/App.jsx", app_jsx)
        await _emit_file_write(agent, "frontend/src/App.jsx", len(app_jsx.splitlines()), event_bus)

        # Edit Sidebar.jsx to add nav item (idempotent)
        await _stream_text("\nAdding nav item to `Sidebar.jsx`...\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "frontend/src/components/Sidebar.jsx", "old_string": "navItems = [...]", "new_string": "navItems = [..., Cost Checker]"}, event_bus)

        sidebar_jsx = Path(self.seed_app_path, "frontend/src/components/Sidebar.jsx").read_text()
        if "CostCheckerIcon" not in sidebar_jsx:
            sidebar_jsx = sidebar_jsx.replace(
                "{ to: '/medications', label: 'Medications', icon: MedicationsIcon },",
                "{ to: '/medications', label: 'Medications', icon: MedicationsIcon },\n  { to: '/cost-checker', label: 'Cost Checker', icon: CostCheckerIcon },",
            )
            cost_checker_icon = '''
function CostCheckerIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}
'''
            sidebar_jsx = sidebar_jsx.rstrip() + "\n" + cost_checker_icon
        self.workspace.write_file("frontend/src/components/Sidebar.jsx", sidebar_jsx)
        await _emit_file_write(agent, "frontend/src/components/Sidebar.jsx", len(sidebar_jsx.splitlines()), event_bus)

        total_lines = len(page_code.splitlines()) + len(app_jsx.splitlines()) + len(sidebar_jsx.splitlines())
        return {
            "output": "Frontend implementation complete: CostCheckerPage with search, results, and navigation",
            "artifacts": [
                "frontend/src/pages/CostCheckerPage.jsx",
                "frontend/src/App.jsx",
                "frontend/src/components/Sidebar.jsx",
            ],
            "tokens_used": 2876,
            "lines_written": total_lines,
        }

    async def _run_qa(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        if self._scenario == "chat_bubble":
            return await self._run_qa_chat(pipeline, task, event_bus)
        agent = task.agent.value

        test_code = '''import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.auth import create_token

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_token(1, "Sarah Johnson")
    return {"Authorization": f"Bearer {token}"}


class TestCostEstimate:
    def test_search_by_drug_name(self, auth_headers):
        """AC1: Member can search for a drug and see copay"""
        response = client.get("/api/cost-estimate?drug_name=metformin", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] >= 1
        assert data["results"][0]["copay_amount"] == 10.0

    def test_results_include_tier_and_coverage(self, auth_headers):
        """AC2: Results show tier, copay, and coverage details"""
        response = client.get("/api/cost-estimate?drug_name=humira", headers=auth_headers)
        data = response.json()
        result = data["results"][0]
        assert "tier" in result
        assert "copay_amount" in result
        assert "prior_auth_required" in result
        assert "step_therapy_required" in result
        assert "quantity_limit" in result

    def test_partial_search(self, auth_headers):
        """AC3: Search supports partial matching"""
        response = client.get("/api/cost-estimate?drug_name=ator", headers=auth_headers)
        data = response.json()
        assert data["total_results"] >= 1

    def test_different_plans_different_copays(self):
        """AC5: Different plans show different copay amounts"""
        # Gold plan member (id=1)
        gold_token = create_token(1, "Sarah Johnson")
        gold_resp = client.get(
            "/api/cost-estimate?drug_name=metformin",
            headers={"Authorization": f"Bearer {gold_token}"}
        )
        # Bronze plan member (id=5)
        bronze_token = create_token(5, "Priya Patel")
        bronze_resp = client.get(
            "/api/cost-estimate?drug_name=metformin",
            headers={"Authorization": f"Bearer {bronze_token}"}
        )

        gold_copay = gold_resp.json()["results"][0]["copay_amount"]
        bronze_copay = bronze_resp.json()["results"][0]["copay_amount"]
        assert bronze_copay > gold_copay  # Bronze has higher copays

    def test_no_results(self, auth_headers):
        """Edge case: drug not found"""
        response = client.get("/api/cost-estimate?drug_name=zzzznotadrug", headers=auth_headers)
        data = response.json()
        assert data["total_results"] == 0
        assert data["results"] == []
'''

        await _stream_text("Writing tests: `tests/test_cost_estimate.py`\n\n```python\n" + test_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/tests/test_cost_estimate.py", test_code)
        await _emit_file_write(agent, "backend/tests/test_cost_estimate.py", len(test_code.splitlines()), event_bus)

        # Simulate running tests
        await _stream_text("\nRunning pytest...\n", agent, event_bus)
        await _emit_tool_call(agent, "run_command", {"command": "cd backend && python -m pytest tests/test_cost_estimate.py -v"}, event_bus)
        await asyncio.sleep(1.0)

        test_report = """```
========================= test session starts =========================
tests/test_cost_estimate.py::TestCostEstimate::test_search_by_drug_name PASSED
tests/test_cost_estimate.py::TestCostEstimate::test_results_include_tier_and_coverage PASSED
tests/test_cost_estimate.py::TestCostEstimate::test_partial_search PASSED
tests/test_cost_estimate.py::TestCostEstimate::test_different_plans_different_copays PASSED
tests/test_cost_estimate.py::TestCostEstimate::test_no_results PASSED
========================= 5 passed in 0.42s ===========================
```
"""
        await _stream_text(test_report, agent, event_bus)

        await event_bus.emit(PipelineEvent(
            type=EventType.TEST_RESULT,
            agent=agent,
            data={"passed": 5, "failed": 0, "total": 5, "status": "all_passed"},
        ))

        return {
            "output": "All 5 tests passed. Cost estimate feature is verified.",
            "artifacts": ["backend/tests/test_cost_estimate.py"],
            "tokens_used": 1654,
            "lines_written": len(test_code.splitlines()),
        }

    # ── Chat Bubble scenario methods ──────────────────────────────────────

    async def _run_pm_chat(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        agent = task.agent.value
        prd = f"""# Product Requirements Document

## Feature: Chat Bubble Assistant

### Problem Statement
Members currently have to navigate through multiple pages to find answers to common questions about their benefits, coverage, and medication costs. This creates friction in the user experience and increases call center volume for simple inquiries that could be answered instantly. A contextual chat bubble provides immediate, personalized answers without leaving the current page.

### Intent
> {pipeline.intent}

### Target Personas
1. **Active Member** — Has ongoing prescriptions, wants quick answers about copays and coverage without navigating away
2. **New Member** — Just enrolled, has many questions about how their plan works and what's covered
3. **Caregiver** — Managing medications for a family member, needs fast answers while reviewing plan details

### User Stories
1. As a member, I want to ask about my copay for a specific medication so I can quickly check costs without leaving my current page
2. As a member, I want to ask about my plan details so I can understand my coverage without navigating to the plan page
3. As a member, I want to open and close the chat at any time so it doesn't interfere with my normal browsing
4. As a member, I want to see a welcome message when I open the chat so I know what questions I can ask

### Acceptance Criteria
- **AC1**: A floating chat bubble is visible on all authenticated pages (bottom-right corner)
- **AC2**: Member can ask about drug costs and receive formulary-based answers with tier and copay info
- **AC3**: Member can ask about their plan and receive plan details
- **AC4**: Chat bubble can be opened and closed with smooth animation
- **AC5**: Responses are accurate across all plan types (Gold, Silver, Bronze) with correct copay amounts

### Non-Functional Requirements
- Response time: chat reply < 500ms
- Accessible: keyboard navigable, screen reader friendly
- Does not obstruct primary page content

### Out of Scope
- Real LLM/AI integration (uses keyword matching for demo)
- Conversation history persistence across sessions
- File or image attachments
- Multi-turn contextual conversations
"""

        await _stream_text(prd, agent, event_bus)
        self.workspace.write_file("prd.md", prd)
        await _emit_file_write(agent, "prd.md", len(prd.splitlines()), event_bus)

        return {
            "output": prd,
            "artifacts": ["prd.md"],
            "tokens_used": 1923,
            "lines_written": len(prd.splitlines()),
        }

    async def _run_tech_lead_chat(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        agent = task.agent.value
        task_plan = """# Task Breakdown & Dependency Graph

## Tasks

### T1: API Endpoint — Chat Message
- **Assignee**: Backend Dev
- **AC**: AC2, AC3
- **Description**: Create `POST /api/chat` endpoint that accepts a message and returns a contextual response based on the member's plan and formulary
- **Dependencies**: None (uses existing models)

### T2: Chat Response Service
- **Assignee**: Backend Dev
- **AC**: AC2, AC3, AC5
- **Description**: Business logic to parse member questions, match keywords against formulary/plan data, and return structured responses
- **Dependencies**: T1

### T3: Frontend — Chat Bubble Component
- **Assignee**: Frontend Dev
- **AC**: AC1, AC4
- **Description**: Floating chat bubble with expandable chat window, message list, and input field
- **Dependencies**: T1 (needs API contract)

### T4: Layout Integration
- **Assignee**: Frontend Dev
- **AC**: AC1
- **Description**: Add ChatBubble component to AppLayout so it appears on all authenticated pages
- **Dependencies**: T3

### T5: Integration Tests
- **Assignee**: QA Engineer
- **AC**: AC1-AC5
- **Description**: pytest tests covering chat responses for drug queries, plan queries, greetings, and edge cases
- **Dependencies**: T1, T2

## Dependency DAG
```mermaid
graph LR
    T1[T1: Chat Endpoint] --> T2[T2: Response Service]
    T1 --> T3[T3: Chat Bubble UI]
    T3 --> T4[T4: Layout Integration]
    T1 --> T5[T5: Integration Tests]
    T2 --> T5
```

## Parallelism
- T3/T4 (Frontend) and T1/T2 (Backend) can proceed in parallel after architect spec
- T5 (Tests) runs after backend is complete
"""

        await _stream_text(task_plan, agent, event_bus)
        self.workspace.write_file("task_plan.md", task_plan)
        await _emit_file_write(agent, "task_plan.md", len(task_plan.splitlines()), event_bus)

        return {
            "output": task_plan,
            "artifacts": ["task_plan.md"],
            "tokens_used": 1187,
            "lines_written": len(task_plan.splitlines()),
        }

    async def _run_architect_chat(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        agent = task.agent.value

        await _emit_tool_call(agent, "list_directory", {"path": ""}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "backend/app/routes/drugs.py"}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "frontend/src/components/AppLayout.jsx"}, event_bus)

        spec = """# Architecture Specification — Chat Bubble Assistant

## API Contract

### `POST /api/chat`

**Request Body:**
```json
{
  "message": "What is my copay for metformin?"
}
```

**Response** `200 OK`:
```json
{
  "response": "Based on your Gold Plan, Metformin (500mg tablet) is a Tier 1 Preferred Generic with a copay of $10.00.",
  "type": "drug_info",
  "data": {
    "drug_name": "Metformin",
    "strength": "500mg",
    "form": "tablet",
    "tier": 1,
    "tier_name": "Preferred Generic",
    "copay_amount": 10.00
  }
}
```

**Response Types:**
| Type | Description |
|------|-------------|
| `text` | General text response (greetings, fallback) |
| `drug_info` | Drug cost lookup with tier/copay data |
| `plan_info` | Plan details response |

## Data Model Changes
None — reuses existing `Member → Plan → Formulary → FormularyDrug → Drug` join path.

## Backend Components
1. **Route**: `app/routes/chat.py` — new router, `POST /api/chat`
2. **Service**: `app/services/chat_service.py` — keyword matching + formulary lookup
3. **Schema**: `app/schemas/chat.py` — request/response models
4. **Registration**: Add router to `app/main.py`

## Frontend Components
1. **Component**: `src/components/ChatBubble.jsx` — floating bubble + expandable chat window
2. **Integration**: Add to `AppLayout.jsx` (NOT a new page or route)

## Request Flow

```mermaid
sequenceDiagram
    participant U as Member
    participant CB as ChatBubble
    participant API as POST /api/chat
    participant SVC as chat_service
    participant DB as SQLite

    U->>CB: Type message
    CB->>API: {"message": "copay for metformin"}
    API->>SVC: handle_message(member_id, message)
    SVC->>DB: JOIN Member → Plan → Formulary → Drug
    DB-->>SVC: FormularyDrug match
    SVC-->>API: {response, type: "drug_info", data}
    API-->>CB: ChatResponse
    CB-->>U: Display response card
```

## Component Spec — ChatBubble

**Layout:**
- Floating circle button: fixed bottom-right (24px margin), 56px diameter
- Chat panel: 384px wide × 480px tall, anchored above button
- Header: "ClearRx Assistant" title + close (X) button
- Message area: scrollable, auto-scrolls to latest
- Input bar: text input + send button

**Message Rendering:**
- User messages: right-aligned, blue background
- Bot messages: left-aligned, gray background
- Drug info messages: include a small card with tier badge + copay amount
- Plan info messages: include plan name and description
"""

        await _stream_text(spec, agent, event_bus)
        self.workspace.write_file("architecture_spec.md", spec)
        await _emit_file_write(agent, "architecture_spec.md", len(spec.splitlines()), event_bus)

        return {
            "output": spec,
            "artifacts": ["architecture_spec.md"],
            "tokens_used": 2034,
            "lines_written": len(spec.splitlines()),
        }

    async def _run_backend_dev_chat(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        agent = task.agent.value

        await _emit_tool_call(agent, "read_file", {"path": "backend/app/routes/drugs.py"}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "backend/app/services/formulary_service.py"}, event_bus)

        # Schema
        schema_code = '''from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    type: str  # "text", "drug_info", "plan_info"
    data: dict | None = None
'''
        await _stream_text("Creating schema: `app/schemas/chat.py`\n\n```python\n" + schema_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/app/schemas/chat.py", schema_code)
        await _emit_file_write(agent, "backend/app/schemas/chat.py", len(schema_code.splitlines()), event_bus)

        # Service
        service_code = '''import re

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.drug import Drug
from app.models.formulary import Formulary, FormularyDrug
from app.models.member import Member

TIER_NAMES = {
    1: "Preferred Generic",
    2: "Non-Preferred Generic",
    3: "Preferred Brand",
    4: "Specialty",
}

GREETING_PATTERNS = re.compile(r"^(hi|hello|hey|help|what can you do)", re.IGNORECASE)
DRUG_PATTERNS = re.compile(r"(?:copay|cost|price|how much)\\s+(?:for|of|is)\\s+(.+)", re.IGNORECASE)
PLAN_PATTERNS = re.compile(r"(my plan|what plan|coverage|what am i|which plan)", re.IGNORECASE)


def handle_message(db: Session, member_id: int, message: str) -> dict:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return {"response": "I couldn\\'t find your member profile.", "type": "text", "data": None}

    plan = member.plan

    # Check for drug cost questions
    drug_match = DRUG_PATTERNS.search(message)
    if drug_match:
        drug_name = drug_match.group(1).strip().rstrip("?.")
        return _lookup_drug(db, member, plan, drug_name)

    # Check for plan questions
    if PLAN_PATTERNS.search(message):
        return _plan_info(plan)

    # Check for greetings
    if GREETING_PATTERNS.search(message):
        return {
            "response": f"Hi {member.first_name}! I can help you with:\\n"
                        f"- Medication costs (try \\"copay for metformin\\")\\n"
                        f"- Plan details (try \\"what plan am I on\\")\\n"
                        f"What would you like to know?",
            "type": "text",
            "data": None,
        }

    return {
        "response": "I can help you with medication costs, plan details, and coverage questions. "
                    "Try asking \\"What is my copay for metformin?\\" or \\"What plan am I on?\\"",
        "type": "text",
        "data": None,
    }


def _lookup_drug(db: Session, member, plan, drug_name: str) -> dict:
    formulary = db.query(Formulary).filter(Formulary.plan_id == plan.id).first()
    if not formulary:
        return {"response": "I couldn\\'t find your plan\\'s formulary.", "type": "text", "data": None}

    search = f"%{drug_name}%"
    entry = (
        db.query(FormularyDrug)
        .join(Drug, FormularyDrug.drug_id == Drug.id)
        .filter(
            FormularyDrug.formulary_id == formulary.id,
            or_(Drug.name.ilike(search), Drug.generic_name.ilike(search), Drug.brand_name.ilike(search)),
        )
        .options(joinedload(FormularyDrug.drug))
        .first()
    )

    if not entry:
        return {
            "response": f"I couldn\\'t find \\"{drug_name}\\" in your plan\\'s formulary.",
            "type": "text",
            "data": None,
        }

    tier_name = TIER_NAMES.get(entry.tier, f"Tier {entry.tier}")
    drug = entry.drug
    return {
        "response": f"Based on your {plan.name}, {drug.name} ({drug.strength} {drug.form}) "
                    f"is a {tier_name} with a copay of ${entry.copay_amount:.2f}.",
        "type": "drug_info",
        "data": {
            "drug_name": drug.name,
            "strength": drug.strength,
            "form": drug.form,
            "tier": entry.tier,
            "tier_name": tier_name,
            "copay_amount": entry.copay_amount,
        },
    }


def _plan_info(plan) -> dict:
    return {
        "response": f"You are enrolled in the {plan.name}. {plan.description}",
        "type": "plan_info",
        "data": {"plan_name": plan.name, "plan_description": plan.description},
    }
'''
        await _stream_text("\nCreating service: `app/services/chat_service.py`\n\n```python\n" + service_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/app/services/chat_service.py", service_code)
        await _emit_file_write(agent, "backend/app/services/chat_service.py", len(service_code.splitlines()), event_bus)

        # Route
        route_code = '''from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_member
from app.database import get_db
from app.models.member import Member
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import handle_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    member: Member = Depends(get_current_member),
):
    result = handle_message(db, member.id, request.message)
    return ChatResponse(**result)
'''
        await _stream_text("\nCreating route: `app/routes/chat.py`\n\n```python\n" + route_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/app/routes/chat.py", route_code)
        await _emit_file_write(agent, "backend/app/routes/chat.py", len(route_code.splitlines()), event_bus)

        # Edit main.py to register the chat router (idempotent — safe to stack with other features)
        await _stream_text("\nRegistering router in `app/main.py`:\n```python\nfrom app.routes import chat\napp.include_router(chat.router)\n```\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "backend/app/main.py", "old_string": "from app.routes import auth, drugs, ...", "new_string": "from app.routes import auth, chat, drugs, ..."}, event_bus)

        main_py = self._patch_backend_main("chat")
        self.workspace.write_file("backend/app/main.py", main_py)
        await _emit_file_write(agent, "backend/app/main.py", len(main_py.splitlines()), event_bus)

        total_lines = len(schema_code.splitlines()) + len(service_code.splitlines()) + len(route_code.splitlines()) + len(main_py.splitlines())
        return {
            "output": "Backend implementation complete: schema, service, route for /api/chat",
            "artifacts": [
                "backend/app/schemas/chat.py",
                "backend/app/services/chat_service.py",
                "backend/app/routes/chat.py",
                "backend/app/main.py",
            ],
            "tokens_used": 3287,
            "lines_written": total_lines,
        }

    async def _run_frontend_dev_chat(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        agent = task.agent.value

        await _emit_tool_call(agent, "read_file", {"path": "frontend/src/components/AppLayout.jsx"}, event_bus)
        await _emit_tool_call(agent, "read_file", {"path": "frontend/src/hooks/useApi.js"}, event_bus)

        bubble_code = r'''import { useCallback, useRef, useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';

const WELCOME_MESSAGE = {
  role: 'assistant',
  content: "Hi! I'm your ClearRx Assistant. I can help you with medication costs, plan details, and coverage questions.\n\nTry asking:\n\u2022 \"What is my copay for metformin?\"\n\u2022 \"What plan am I on?\"",
  type: 'text',
  data: null,
};

const TIER_COLORS = {
  1: 'bg-emerald-100 text-emerald-800',
  2: 'bg-blue-100 text-blue-800',
  3: 'bg-amber-100 text-amber-800',
  4: 'bg-red-100 text-red-800',
};

export function ChatBubble() {
  const { post } = useApi();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setLoading(true);
    try {
      const data = await post('/api/chat', { message: text });
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response, type: data.type, data: data.data },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.', type: 'text' },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, post]);

  return (
    <>
      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[480px] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 bg-primary-700 text-white flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-400 rounded-full" />
              <span className="font-medium text-sm">ClearRx Assistant</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-white/80 hover:text-white">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ${
                    msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-800'
                  }`}
                >
                  {msg.content}
                  {msg.type === 'drug_info' && msg.data && (
                    <div className="mt-2 p-2 bg-white rounded-lg border border-slate-200 text-slate-700">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{msg.data.drug_name}</span>
                        <span
                          className={`text-xs px-1.5 py-0.5 rounded-full ${TIER_COLORS[msg.data.tier] || ''}`}
                        >
                          {msg.data.tier_name}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {msg.data.strength} {msg.data.form}
                      </div>
                      <div className="text-lg font-bold text-primary-700 mt-1">
                        ${msg.data.copay_amount.toFixed(2)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 rounded-xl px-4 py-2 text-sm text-slate-400">
                  <span className="inline-flex gap-1">
                    <span className="animate-bounce">&middot;</span>
                    <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>&middot;</span>
                    <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>&middot;</span>
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-slate-200 flex-shrink-0">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Ask about your medications..."
                className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="px-3 py-2 bg-primary-700 text-white rounded-lg hover:bg-primary-800 disabled:opacity-40 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Bubble */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary-700 hover:bg-primary-800 text-white rounded-full shadow-lg flex items-center justify-center z-50 transition-transform hover:scale-105"
      >
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        )}
      </button>
    </>
  );
}
'''

        await _stream_text("Creating component: `src/components/ChatBubble.jsx`\n\n```jsx\n" + bubble_code + "```\n", agent, event_bus)
        self.workspace.write_file("frontend/src/components/ChatBubble.jsx", bubble_code)
        await _emit_file_write(agent, "frontend/src/components/ChatBubble.jsx", len(bubble_code.splitlines()), event_bus)

        # Edit AppLayout.jsx to add ChatBubble (idempotent)
        await _stream_text("\nAdding ChatBubble to `AppLayout.jsx`...\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "frontend/src/components/AppLayout.jsx", "old_string": "import { Header }...", "new_string": "import { ChatBubble }..."}, event_bus)

        layout_jsx = Path(self.seed_app_path, "frontend/src/components/AppLayout.jsx").read_text()
        if "ChatBubble" not in layout_jsx:
            layout_jsx = layout_jsx.replace(
                "import { Sidebar } from './Sidebar';\nimport { Header } from './Header';",
                "import { Sidebar } from './Sidebar';\nimport { Header } from './Header';\nimport { ChatBubble } from './ChatBubble';",
            )
            layout_jsx = layout_jsx.replace(
                "        </main>\n      </div>\n    </div>",
                "        </main>\n      </div>\n      <ChatBubble />\n    </div>",
            )
        self.workspace.write_file("frontend/src/components/AppLayout.jsx", layout_jsx)
        await _emit_file_write(agent, "frontend/src/components/AppLayout.jsx", len(layout_jsx.splitlines()), event_bus)

        total_lines = len(bubble_code.splitlines()) + len(layout_jsx.splitlines())
        return {
            "output": "Frontend implementation complete: ChatBubble component with floating UI and AppLayout integration",
            "artifacts": [
                "frontend/src/components/ChatBubble.jsx",
                "frontend/src/components/AppLayout.jsx",
            ],
            "tokens_used": 2654,
            "lines_written": total_lines,
        }

    async def _run_qa_chat(self, pipeline: PipelineState, task: PipelineTask, event_bus: EventBus) -> dict[str, Any]:
        agent = task.agent.value

        test_code = '''import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_token

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_token(1, "Sarah Johnson")
    return {"Authorization": f"Bearer {token}"}


class TestChat:
    def test_drug_cost_query(self, auth_headers):
        """AC2: Member can ask about drug costs"""
        response = client.post("/api/chat", json={"message": "What is my copay for metformin?"}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "drug_info"
        assert "metformin" in data["response"].lower()
        assert data["data"]["copay_amount"] == 10.0

    def test_plan_query(self, auth_headers):
        """AC3: Chat responds to plan questions"""
        response = client.post("/api/chat", json={"message": "What plan am I on?"}, headers=auth_headers)
        data = response.json()
        assert data["type"] == "plan_info"
        assert "Gold" in data["response"]

    def test_greeting(self, auth_headers):
        """AC4: Chat handles greetings"""
        response = client.post("/api/chat", json={"message": "Hello"}, headers=auth_headers)
        data = response.json()
        assert data["type"] == "text"
        assert "help" in data["response"].lower() or "Hi" in data["response"]

    def test_unknown_query(self, auth_headers):
        """Fallback for unrecognized queries"""
        response = client.post("/api/chat", json={"message": "asdfghjkl random text"}, headers=auth_headers)
        data = response.json()
        assert data["type"] == "text"
        assert "help" in data["response"].lower() or "medication" in data["response"].lower()

    def test_different_plans_different_copays(self):
        """AC5: Different plans return different copay data"""
        gold_token = create_token(1, "Sarah Johnson")
        gold_resp = client.post(
            "/api/chat",
            json={"message": "copay for metformin"},
            headers={"Authorization": f"Bearer {gold_token}"},
        )
        bronze_token = create_token(5, "Priya Patel")
        bronze_resp = client.post(
            "/api/chat",
            json={"message": "copay for metformin"},
            headers={"Authorization": f"Bearer {bronze_token}"},
        )
        gold_copay = gold_resp.json()["data"]["copay_amount"]
        bronze_copay = bronze_resp.json()["data"]["copay_amount"]
        assert bronze_copay > gold_copay
'''

        await _stream_text("Writing tests: `tests/test_chat.py`\n\n```python\n" + test_code + "```\n", agent, event_bus)
        self.workspace.write_file("backend/tests/test_chat.py", test_code)
        await _emit_file_write(agent, "backend/tests/test_chat.py", len(test_code.splitlines()), event_bus)

        # Simulate running tests
        await _stream_text("\nRunning pytest...\n", agent, event_bus)
        await _emit_tool_call(agent, "run_command", {"command": "cd backend && python -m pytest tests/test_chat.py -v"}, event_bus)
        await asyncio.sleep(1.0)

        test_report = """```
========================= test session starts =========================
tests/test_chat.py::TestChat::test_drug_cost_query PASSED
tests/test_chat.py::TestChat::test_plan_query PASSED
tests/test_chat.py::TestChat::test_greeting PASSED
tests/test_chat.py::TestChat::test_unknown_query PASSED
tests/test_chat.py::TestChat::test_different_plans_different_copays PASSED
========================= 5 passed in 0.38s ===========================
```
"""
        await _stream_text(test_report, agent, event_bus)

        await event_bus.emit(PipelineEvent(
            type=EventType.TEST_RESULT,
            agent=agent,
            data={"passed": 5, "failed": 0, "total": 5, "status": "all_passed"},
        ))

        return {
            "output": "All 5 tests passed. Chat bubble feature is verified.",
            "artifacts": ["backend/tests/test_chat.py"],
            "tokens_used": 1598,
            "lines_written": len(test_code.splitlines()),
        }
