"""Mock agent runner that simulates all 7 agents with canned output and realistic delays."""

from __future__ import annotations

import asyncio
import os
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

    async def run(
        self,
        pipeline: PipelineState,
        task: PipelineTask,
        event_bus: EventBus,
    ) -> dict[str, Any]:
        # Deployer is handled by the shared DeployRunner
        if task.agent == AgentRole.DEPLOYER and self.deploy_runner:
            return await self.deploy_runner.run(pipeline, task, event_bus)

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
```
T1 (API) ──► T2 (Service)
    │
    ├──────► T3 (Page) ──► T4 (Nav)
    │
    └──────► T5 (Tests)
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

        # Actually edit main.py to register the router
        await _stream_text("\nRegistering router in `app/main.py`:\n```python\nfrom app.routes import cost_estimate\napp.include_router(cost_estimate.router)\n```\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "backend/app/main.py", "old_string": "from app.routes import auth, drugs, ...", "new_string": "from app.routes import auth, cost_estimate, drugs, ..."}, event_bus)

        main_py = Path(self.seed_app_path, "backend/app/main.py").read_text()
        main_py = main_py.replace(
            "from app.routes import auth, drugs, formulary, members, plans",
            "from app.routes import auth, cost_estimate, drugs, formulary, members, plans",
        )
        main_py = main_py.replace(
            "app.include_router(formulary.router)",
            "app.include_router(formulary.router)\napp.include_router(cost_estimate.router)",
        )
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

        # Actually edit App.jsx to add route
        await _stream_text("\nAdding route to `App.jsx`...\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "frontend/src/App.jsx", "old_string": "import { MedicationsPage }...", "new_string": "import { CostCheckerPage }..."}, event_bus)

        app_jsx = Path(self.seed_app_path, "frontend/src/App.jsx").read_text()
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

        # Actually edit Sidebar.jsx to add nav item
        await _stream_text("\nAdding nav item to `Sidebar.jsx`...\n", agent, event_bus)
        await _emit_tool_call(agent, "edit_file", {"path": "frontend/src/components/Sidebar.jsx", "old_string": "navItems = [...]", "new_string": "navItems = [..., Cost Checker]"}, event_bus)

        sidebar_jsx = Path(self.seed_app_path, "frontend/src/components/Sidebar.jsx").read_text()
        sidebar_jsx = sidebar_jsx.replace(
            "{ to: '/medications', label: 'Medications', icon: MedicationsIcon },",
            "{ to: '/medications', label: 'Medications', icon: MedicationsIcon },\n  { to: '/cost-checker', label: 'Cost Checker', icon: CostCheckerIcon },",
        )
        # Add the CostCheckerIcon component at the end
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
