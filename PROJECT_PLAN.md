# Project Plan — PBM Agent Swarm

## Phase 1: Seed Application

**Goal**: A working PBM platform that agents will read and extend. Must run end-to-end.

### Phase 1A: Backend Foundation

- [x] Project scaffolding: `seed-app/backend/` with FastAPI, requirements.txt, app structure
- [x] Database layer: SQLAlchemy 2.0 engine, session factory, Base model (`database.py`)
- [x] Domain models:
  - `Member` — id, first_name, last_name, email, date_of_birth, plan_id
  - `Plan` — id, name, description, tier structure (JSON or related table)
  - `Drug` — id, name, ndc_code, generic_name, brand_name, strength, form, manufacturer
  - `Formulary` — id, plan_id, name, effective_date
  - `FormularyDrug` — formulary_id, drug_id, tier (1-4), copay_amount, prior_auth_required, quantity_limit, step_therapy_required
  - `Pharmacy` — id, name, address, city, state, zip, phone, pharmacy_type (retail/mail_order)
  - `Prescriber` — id, first_name, last_name, npi, specialty, phone
- [x] Pydantic v2 schemas for all models
- [x] Auth system: mock JWT login (`POST /api/auth/login` — email lookup, returns token with member_id)
- [x] Auth dependency: `get_current_member` extracts member from token
- [x] Routes + Services:
  - `GET /api/members/me` — current member profile + plan summary
  - `GET /api/plans/{id}` — plan details with formulary info
  - `GET /api/drugs` — list/search drugs (query param for search)
  - `GET /api/drugs/{id}` — drug detail
  - `GET /api/formulary/{plan_id}` — formulary for a plan with tier/copay info
- [x] Seed data script (`seed.py`):
  - 50 real drugs (FDA NDC names: metformin, lisinopril, atorvastatin, lipitor, omeprazole, amlodipine, sertraline, etc.)
  - Generic↔brand relationships (e.g., atorvastatin↔Lipitor, sertraline↔Zoloft)
  - 3 plans: Gold ($10/$25/$50/$75 copays by tier), Silver ($15/$35/$65/$100), Bronze ($20/$45/$80/$125)
  - 3 formularies (one per plan) with drug→tier mappings
  - 5 demo members (each assigned to a plan)
  - 5 pharmacies (mix of retail and mail order)
  - 5 prescribers (different specialties)
- [x] Auto-seed on startup (create tables + populate if empty)
- [x] Health check endpoint: `GET /api/health`

### Phase 1B: Frontend Foundation

- [x] Project scaffolding: `seed-app/frontend/` with Vite + React 18 + Tailwind
- [x] Tailwind config with healthcare design tokens:
  - Primary: deep blue (#1e40af → #3b82f6 range)
  - Accent: teal (#0d9488)
  - Neutral: slate grays
  - Clean, trustworthy feel — white backgrounds, subtle borders, good spacing
- [x] Auth system:
  - `AuthContext` — stores token + member info, provides login/logout
  - `useAuth` hook
  - Login page — email-only (matches mock JWT backend)
  - Protected route wrapper
- [x] `useApi` hook — wraps fetch with Authorization header, base URL, error handling
- [x] Layout:
  - `AppLayout` with sidebar + header + main content area
  - `Sidebar` — nav links (Dashboard, My Plan, Medications), member name at bottom
  - `Header` — page title, breadcrumb
- [x] Pages:
  - `LoginPage` — clean email login form
  - `DashboardPage` — member greeting, plan summary card, quick stats
  - `PlanPage` — plan details, formulary tier breakdown
  - `MedicationsPage` — searchable drug list from the formulary
- [x] React Router v6 setup with layout outlet pattern
- [x] API proxy config in Vite (proxy `/api` to `:8000`)

### Phase 1C: Integration & Polish

- [x] `seed-app/README.md` — patterns guide for agents: file structure, how to add a route, how to add a page, naming conventions, database patterns
- [x] Makefile targets: `make seed-backend`, `make seed-frontend`, `make dev`
- [ ] docker-compose.yml (optional — deferred to Phase 5)
- [x] End-to-end verification: login → dashboard → plan → medications all work

### Phase 1 Acceptance Criteria

- `make dev` starts backend (:8000) and frontend (:5173)
- Database seeds automatically on first run
- Login as demo member → see dashboard with plan summary
- All API endpoints return correct data
- Code is clean and exemplary (agents will read it)
- README documents patterns clearly

---

## Phase 2: Orchestrator Skeleton

**Goal**: DAG executor and WebSocket event bus, working with mocked agent responses.

- [x] Project scaffolding: `orchestrator/` with FastAPI + requirements
- [x] Task state machine: QUEUED → ASSIGNED → IN_PROGRESS → DONE | FAILED
- [x] DAG definition: declare 7 tasks with dependency edges (PM→TL→Arch→[BE,FE]→QA→Deployer)
- [x] Async DAG executor: polls for tasks whose deps are satisfied, runs them
- [x] WebSocket endpoint: `/ws` — clients connect, receive all events
- [x] Event bus: publish events `{ type, agent, data, timestamp }`
  - Event types: `task_state_change`, `agent_output`, `tool_call`, `file_write`, `test_result`, `pipeline_start`, `pipeline_complete`
- [x] Mock agent runner: simulates each agent with canned output + realistic delays
- [x] REST endpoints:
  - `POST /api/run` — accepts `{ intent }`, starts pipeline
  - `GET /api/status` — current pipeline state
  - `GET /api/artifacts` — list generated files
  - `GET /api/artifacts/{path}` — file contents
- [x] Workspace management: create temp directory, track files
- [x] Agent tool definitions (interfaces only, wired in Phase 4):
  - `read_file`, `write_file`, `edit_file`, `list_directory`
  - `run_command` (Backend Dev + QA only)

### Phase 2 Acceptance Criteria

- `POST /api/run` with an intent triggers the full mocked pipeline
- WebSocket client receives all state transitions and mock agent output
- Pipeline completes in correct DAG order
- Parallel tasks (Backend Dev + Frontend Dev) run concurrently
- Workspace directory accumulates mock artifacts

---

## Phase 3: Dashboard

**Goal**: Real-time visualization of the orchestrator pipeline.

- [x] Project scaffolding: `dashboard/` with Vite + React 18 + Tailwind + Framer Motion
- [x] WebSocket hook: connect to orchestrator, parse events, update state
- [x] Top: Pipeline DAG (react-flow)
  - 6 nodes (one per agent), edges for dependencies
  - Animated state colors: gray=queued, blue=in-progress, green=done, red=failed
  - Subtle glow on active node (Framer Motion)
- [x] Left panel (25%): PRD Panel
  - Renders PM agent's PRD as streaming markdown (react-markdown)
  - Auto-scrolls as content arrives
- [x] Center panel (50%): DAG + Live Agent Feed
  - DAG visualization at top, tabbed agent output below
  - Streaming output with syntax highlighting (react-syntax-highlighter)
  - Auto-scrolls as content streams, auto-switches to active agent
  - Distinguishes code blocks vs. text vs. tool calls
- [x] Right panel (25%): Artifact Explorer
  - File tree that grows as agents write files
  - Click file to view contents with syntax highlighting (expandable inline)
- [x] Bottom bar: Metrics
  - Tasks complete (X/Y)
  - Tokens used
  - Elapsed time
  - Lines of code generated
  - Test results (when available)
  - Progress bar
- [x] Input bar: text field to enter business intent, start button, WS connection indicator
- [x] Visual polish: ShadCN-inspired light theme, Framer Motion transitions, mermaid diagrams, GFM markdown

### Phase 3 Acceptance Criteria

- Dashboard connects to orchestrator WebSocket
- Visualizes full mocked pipeline in real time
- All panels update correctly as events stream in
- Looks polished and professional
- Intent input → pipeline visualization → completion, all visible

---

## Phase 4: Real Agent Implementations

**Goal**: Replace mocks with real Claude API calls, one agent at a time.

### Phase 4A: Product Manager Agent

- [x] System prompt (`prompts/product_manager.md`): role, output format (structured PRD with problem, personas, user stories, acceptance criteria, NFRs, out-of-scope)
- [x] Agent runner: Anthropic SDK streaming call with the PM prompt
- [x] Tools: `read_file`, `list_directory` (reads seed app for context)
- [ ] Test: run PM agent standalone, verify PRD quality

### Phase 4B: Tech Lead Agent

- [x] System prompt: decomposes PRD into task DAG
- [x] Tools: `read_file` (reads PRD)

### Phase 4C: Architect Agent

- [x] System prompt: designs API contracts, data model changes, component specs
- [x] Tools: `read_file`, `list_directory` (reads seed app structure)

### Phase 4D: Backend Dev Agent

- [x] System prompt: implements backend code following seed patterns
- [x] Tools: `read_file`, `write_file`, `edit_file`, `list_directory`, `run_command`

### Phase 4E: Frontend Dev Agent

- [x] System prompt: implements frontend following seed patterns
- [x] Tools: `read_file`, `write_file`, `edit_file`, `list_directory`

### Phase 4F: QA Engineer Agent

- [x] System prompt: writes and runs pytest tests
- [x] Tools: `read_file`, `write_file`, `run_command`

### Phase 4G: Deployer Agent (Human-in-the-Loop)

- [x] `DeployRunner` — standalone runner (no LLM), approval gate via `asyncio.Event`
- [x] `WAITING_APPROVAL` task status with amber DAG visualization
- [x] `POST /api/deploy/approve` and `/reject` endpoints
- [x] Dashboard `DeployApproval` component — file list, preview, approve/reject buttons
- [x] Wired into both mock and real pipelines (shared runner)
- [x] `make revert` target to undo deployed changes (`git checkout` + `git clean`)
- [x] Mock runner produces deployable code (real edits to main.py, App.jsx, Sidebar.jsx)
- [x] Mermaid diagram for TL dependency DAG (replaced ASCII art)
- [x] Draggable resize handles between dashboard panel columns

### Phase 4 Infrastructure

- [x] `ClaudeAgentRunner` with Anthropic SDK streaming + tool use loop
- [x] `ToolExecutor` — executes tools against workspace + seed app
- [x] `context.py` — injects seed app files + prior agent outputs per role
- [x] Config toggle: `USE_MOCK=true/false`
- [x] `make demo-live` target (requires `ANTHROPIC_API_KEY`)

### Phase 4 Acceptance Criteria

- Each agent produces high-quality, contextual output
- Agents follow seed app patterns faithfully
- Streaming works — dashboard shows token-by-token output
- Full pipeline runs with real API calls

---

## Phase 5: End-to-End Demo & Polish

**Goal**: Complete run producing "Drug Cost Checker" feature, polished for presentation.

- [ ] End-to-end run: input "Members should be able to check what their medications will cost before filling them"
- [ ] Verify the generated Drug Cost Checker feature works:
  - New API endpoint for cost estimation
  - Frontend page for cost lookup
  - Tests pass
- [ ] Tune agent prompts for output quality and speed
- [ ] Optimize for < 4 minute total runtime
- [ ] Dashboard polish: loading states, error handling, edge cases
- [ ] Demo script: step-by-step guide for the presenter
- [ ] docker-compose.yml for one-command full-stack startup
- [ ] Record backup video in case of live demo failure

### Phase 5 Acceptance Criteria

- Full pipeline completes in < 4 minutes
- Generated Drug Cost Checker feature works in the seed app
- Dashboard visualization is smooth and professional
- Demo is repeatable and reliable
- Presenter has a clear script to follow
