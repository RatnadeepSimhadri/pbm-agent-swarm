# PBM Agent Swarm

A multi-agent developer workflow that takes a one-line business intent and ships a working feature into an existing Pharmacy Benefit Management (PBM) codebase. A real-time dashboard shows AI agents collaborating live.

Built for executive presentations.

## Architecture

```
User types business intent
        │
        ▼
┌──────────────────┐     ┌─────────────────────────────┐
│  Dashboard :5174 │◄────│   Orchestrator :8001        │
│  React + Vite    │ WS  │   FastAPI + Anthropic SDK   │
│                  │     │                             │
│  • Pipeline DAG  │     │   PM → Tech Lead → Architect│
│  • PRD Panel     │     │         ┌─────┴─────┐      │
│  • Agent Feed    │     │     Backend Dev  Frontend Dev│
│  • Artifacts     │     │         └─────┬─────┘      │
│  • Metrics       │     │              QA             │
│                  │     │              ▼              │
│                  │     │        Deployer (HITL)      │
└──────────────────┘     └──────────┬──────────────────┘
                                    │ Deploys to
                                    ▼
                         ┌──────────────────────┐
                         │  Seed App :8000/:5173 │
                         │  FastAPI + React      │
                         │  The PBM app agents   │
                         │  extend with features │
                         └──────────────────────┘
```

**7 agents run in DAG order:**

1. **Product Manager** — Generates a PRD from the business intent
2. **Tech Lead** — Breaks the PRD into a task dependency graph
3. **Architect** — Designs API contracts, data model, component specs
4. **Backend Dev** — Implements FastAPI routes, services, schemas
5. **Frontend Dev** — Implements React components and pages
6. **QA Engineer** — Writes and runs pytest tests
7. **Deployer** — Human-in-the-loop approval gate, copies files to seed app

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (with npm)
- **Git**

## Setup

```bash
git clone https://github.com/RatnadeepSimhadri/pbm-agent-swarm.git
cd pbm-agent-swarm
make install
```

This creates Python virtual environments and installs all npm/pip dependencies for all 4 components.

## Running

### Mock Demo (no API key needed)

```bash
make demo
```

Starts the orchestrator (`:8001`) and dashboard (`:5174`). Open http://localhost:5174, pick a scenario preset (Drug Cost Checker or Chat Bubble), and click **Build Feature**. The pipeline runs with canned agent outputs that simulate real Claude responses.

After the pipeline completes, approve the deployment in the dashboard. The generated feature gets copied into the seed app.

Then start the seed app to see the feature working:

```bash
make dev
```

Open http://localhost:5173 and log in with any demo member email (e.g., `sarah.johnson@email.com`).

### Live Demo (real Claude agents)

```bash
export ANTHROPIC_API_KEY=sk-...
make demo-live
```

Same flow but agents make real Anthropic API calls with streaming output.

### Individual Components

```bash
make seed-backend     # Backend on :8000
make seed-frontend    # Frontend on :5173
make orchestrator     # Orchestrator on :8001
make dashboard        # Dashboard on :5174
```

### Other Commands

```bash
make seed-db          # Re-seed the database
make test             # Run backend pytest suite
make revert           # Undo deployed changes to seed-app
make clean            # Remove all generated files (venvs, node_modules, db)
```

## Demo Scenarios

The mock demo includes two preset scenarios:

| Scenario | Intent | What it builds |
|----------|--------|----------------|
| **Drug Cost Checker** | "Members should be able to check what their medications will cost before filling them" | New page with drug search, copay/tier display, sidebar nav link |
| **Chat Bubble** | "Add a chat bubble to the page where users can ask questions about their medications and coverage" | Floating chat component in bottom-right, keyword-based Q&A against formulary data |

## Tech Stack

| Component | Stack |
|-----------|-------|
| Seed Backend | Python, FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite |
| Seed Frontend | React 18, Vite, Tailwind CSS, React Router v6 |
| Orchestrator | Python, FastAPI, asyncio, Anthropic SDK, WebSockets |
| Dashboard | React 18, Vite, Tailwind CSS, Framer Motion, react-flow, react-markdown |

## Demo Members

| Name | Email | Plan |
|------|-------|------|
| Sarah Johnson | sarah.johnson@email.com | Gold |
| Michael Chen | michael.chen@email.com | Gold |
| Emily Rodriguez | emily.rodriguez@email.com | Silver |
| James Williams | james.williams@email.com | Silver |
| Priya Patel | priya.patel@email.com | Bronze |
