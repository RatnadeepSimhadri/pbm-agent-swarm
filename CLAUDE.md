# PBM Agent Swarm

## Mission

Demonstrate a multi-agent developer workflow — AI agents take a one-line business intent and ship a working feature into an existing Pharmacy Benefit Management (PBM) codebase. A real-time dashboard shows the agents collaborating live. Built for an executive presentation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User / Presenter                           │
│                                                                     │
│   Types: "Members should be able to check what their medications   │
│           will cost before filling them"                            │
└──────────────┬──────────────────────────────────┬───────────────────┘
               │                                  │
               ▼                                  ▼
┌──────────────────────────┐     ┌────────────────────────────────────┐
│     Dashboard (:5174)    │◄────│     Orchestrator (:8001)           │
│                          │ WS  │                                    │
│  React + Vite + Tailwind │     │  FastAPI + Anthropic SDK           │
│  Framer Motion           │     │                                    │
│  react-flow (DAG)        │     │  ┌──────────────────────────────┐  │
│  react-syntax-highlighter│     │  │      DAG Executor            │  │
│  react-markdown          │     │  │                              │  │
│                          │     │  │  PM ─► Tech Lead ─► Architect│  │
│  Panels:                 │     │  │                    │         │  │
│   • Pipeline DAG (top)   │     │  │              ┌─────┴─────┐   │  │
│   • PRD (left 40%)       │     │  │              ▼           ▼   │  │
│   • Agent Feed (center)  │     │  │          Backend     Frontend│  │
│   • Artifacts (right 20%)│     │  │           Dev          Dev   │  │
│   • Metrics (bottom)     │     │  │              └─────┬─────┘   │  │
│                          │     │  │                    ▼         │  │
│                          │     │  │                   QA         │  │
│                          │     │  │                    ▼         │  │
│                          │     │  │              Deployer (HITL) │  │
│                          │     │  └──────────────────────────────┘  │
│                          │     │                                    │
│                          │     │  Human approves → files copied     │
│                          │     │  from workspace into seed-app/     │
└──────────────────────────┘     └──────────────┬─────────────────────┘
                                                │
                                                │ Modifies
                                                ▼
                                 ┌──────────────────────────┐
                                 │   Seed App (:8000/:5173) │
                                 │                          │
                                 │  Backend:  FastAPI +     │
                                 │    SQLAlchemy + SQLite    │
                                 │  Frontend: React + Vite  │
                                 │    + Tailwind             │
                                 │                          │
                                 │  The baseline PBM app    │
                                 │  that agents extend      │
                                 └──────────────────────────┘
```

## Tech Stack

| Component        | Stack                                                              |
|------------------|--------------------------------------------------------------------|
| Seed Backend     | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite, pytest |
| Seed Frontend    | React 18, Vite, Tailwind CSS, React Router v6                     |
| Orchestrator     | Python 3.11+, FastAPI, asyncio, anthropic SDK, websockets          |
| Dashboard        | React 18, Vite, Tailwind CSS, Framer Motion, react-syntax-highlighter, react-markdown, react-flow |
| Dev Orchestration| Makefile + docker-compose                                          |
| AI Model         | claude-sonnet-4-6 (via Anthropic Python SDK, streaming)            |

## Repo Layout

```
pbm-agent-swarm/
├── CLAUDE.md                  # This file — project context
├── PROJECT_PLAN.md            # Phased delivery plan
├── Makefile                   # Top-level dev commands
├── docker-compose.yml         # Full-stack orchestration
│
├── seed-app/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI app, router registration
│   │   │   ├── config.py      # Settings / env config
│   │   │   ├── database.py    # SQLAlchemy engine + session
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   ├── schemas/       # Pydantic v2 schemas
│   │   │   ├── routes/        # FastAPI routers (thin)
│   │   │   ├── services/      # Business logic layer
│   │   │   └── seed.py        # Database seeding script
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── README.md          # Patterns guide (agents read this)
│   └── frontend/
│       ├── src/
│       │   ├── main.jsx
│       │   ├── App.jsx         # Routes
│       │   ├── components/     # Shared components
│       │   ├── pages/          # Route pages
│       │   ├── hooks/          # useApi, useAuth
│       │   ├── contexts/       # AuthContext
│       │   └── lib/            # Utilities
│       ├── index.html
│       ├── tailwind.config.js
│       ├── vite.config.js
│       └── package.json
│
├── orchestrator/
│   ├── app/
│   │   ├── main.py             # FastAPI app + WebSocket endpoint
│   │   ├── dag.py              # DAG executor + task state machine
│   │   ├── agents/             # Agent runner (Anthropic SDK calls)
│   │   ├── tools/              # File system + command tools
│   │   ├── workspace.py        # Workspace management
│   │   └── events.py           # WebSocket event bus
│   ├── prompts/                # One .md file per agent
│   │   ├── product_manager.md
│   │   ├── tech_lead.md
│   │   ├── architect.md
│   │   ├── backend_dev.md
│   │   ├── frontend_dev.md
│   │   └── qa_engineer.md
│   └── requirements.txt
│
└── dashboard/
    ├── src/
    │   ├── main.jsx
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── PipelineDAG.jsx     # react-flow DAG visualization
    │   │   ├── PRDPanel.jsx        # Streaming markdown render
    │   │   ├── AgentFeed.jsx       # Tabbed agent output
    │   │   ├── ArtifactExplorer.jsx# File tree + viewer
    │   │   └── MetricsBar.jsx      # Bottom stats bar
    │   ├── hooks/
    │   │   └── useWebSocket.js     # WS connection + event handling
    │   └── lib/
    ├── index.html
    ├── tailwind.config.js
    ├── vite.config.js
    └── package.json
```

## Conventions

### Backend (Python)

- **Routes are thin** — validate input, call service, return response. No business logic in routes.
- **Services hold logic** — each domain gets a service module (e.g., `services/plan_service.py`).
- **Models use SQLAlchemy 2.0** declarative style with `mapped_column`.
- **Schemas use Pydantic v2** with `model_config = ConfigDict(from_attributes=True)`.
- **Dependency injection** via FastAPI `Depends()` for DB sessions and auth.
- **Naming**: snake_case everywhere. Files named after their domain (e.g., `models/member.py`).

### Frontend (React)

- **Functional components only**, hooks for state/effects.
- **`useApi` hook** wraps `fetch` with auth token injection and error handling.
- **Tailwind utility classes** — no CSS files. Custom design tokens in `tailwind.config.js`.
- **React Router v6** with `<Outlet>` layout pattern.
- **File naming**: PascalCase for components (`MemberDashboard.jsx`), camelCase for hooks/utils.

### Orchestrator

- **One agent = one system prompt file** in `prompts/`. Easy to iterate.
- **All agent calls use streaming** via Anthropic SDK.
- **WebSocket events** follow `{ type, agent, data, timestamp }` shape.
- **DAG tasks** follow state machine: `QUEUED → ASSIGNED → IN_PROGRESS → DONE | FAILED`.

## How to Run

```bash
# Full stack (when docker-compose is ready)
make dev

# Individual components
make seed-backend     # Backend on :8000
make seed-frontend    # Frontend on :5173
make orchestrator     # Orchestrator on :8001
make dashboard        # Dashboard on :5174

# Seed the database
make seed-db

# Run tests
make test
```

## Environment Variables

```
ANTHROPIC_API_KEY=sk-...    # Required for orchestrator
```

## Key Design Decisions

1. **Seed app quality is critical** — agents read it for patterns. Write exemplary code.
2. **Drug Cost Checker is the demo feature** — do NOT pre-build it in the seed app.
3. **Agent prompts are separate files** — easy to tune without touching code.
4. **Streaming everywhere** — dashboard must show token-by-token output.
5. **Demo runtime target** — full pipeline in under 4 minutes.
6. **SQLite** — no external DB dependency, makes demo portable.
