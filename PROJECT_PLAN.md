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
- [x] DAG definition: declare 6 tasks with dependency edges (PM→TL→Arch→[BE,FE]→QA)
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

- [ ] Project scaffolding: `dashboard/` with Vite + React 18 + Tailwind + Framer Motion
- [ ] WebSocket hook: connect to orchestrator, parse events, update state
- [ ] Top: Pipeline DAG (react-flow)
  - 6 nodes (one per agent), edges for dependencies
  - Animated state colors: gray=queued, blue=in-progress, green=done, red=failed
  - Subtle glow on active node (Framer Motion)
- [ ] Left panel (40%): PRD Panel
  - Renders PM agent's PRD as streaming markdown (react-markdown)
  - Typewriter effect as content arrives
- [ ] Center panel (40%): Live Agent Feed
  - Tabs per agent (click to switch)
  - Streaming output with syntax highlighting (react-syntax-highlighter)
  - Auto-scrolls as content streams
  - Distinguishes thinking vs. code output
- [ ] Right panel (20%): Artifact Explorer
  - File tree that grows as agents write files
  - Click file to view contents with syntax highlighting
- [ ] Bottom bar: Metrics
  - Tasks complete (X/Y)
  - Tokens used
  - Elapsed time
  - Lines of code generated
  - Acceptance criteria status (AC1 ✅ AC2 ⏳ ...)
- [ ] Input bar: text field to enter business intent, start button
- [ ] Visual polish: smooth transitions, professional color scheme, exec-ready

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

- [ ] System prompt (`prompts/product_manager.md`): role, output format (structured PRD with problem, personas, user stories, acceptance criteria, NFRs, out-of-scope)
- [ ] Agent runner: Anthropic SDK streaming call with the PM prompt
- [ ] Tools: `read_file`, `list_directory` (reads seed app for context)
- [ ] Output: PRD as markdown + structured JSON
- [ ] Test: run PM agent standalone, verify PRD quality

### Phase 4B: Tech Lead Agent

- [ ] System prompt: decomposes PRD into task DAG
- [ ] Output: task list with dependencies, mapped to acceptance criteria, parallelism identified
- [ ] Tools: `read_file` (reads PRD)

### Phase 4C: Architect Agent

- [ ] System prompt: designs API contracts, data model changes, component specs
- [ ] Tools: `read_file`, `list_directory` (reads seed app structure)
- [ ] Output: OpenAPI-style API spec, model migration notes, frontend component tree

### Phase 4D: Backend Dev Agent

- [ ] System prompt: implements backend code following seed patterns
- [ ] Tools: `read_file`, `write_file`, `edit_file`, `list_directory`, `run_command`
- [ ] Output: new route/service/model files, edits to main.py
- [ ] Must follow existing patterns (route→service, Pydantic schemas, etc.)

### Phase 4E: Frontend Dev Agent

- [ ] System prompt: implements frontend following seed patterns
- [ ] Tools: `read_file`, `write_file`, `edit_file`, `list_directory`
- [ ] Output: new pages/components, edits to App.jsx and Sidebar.jsx
- [ ] Must match existing Tailwind theme

### Phase 4F: QA Engineer Agent

- [ ] System prompt: writes and runs pytest tests
- [ ] Tools: `read_file`, `write_file`, `run_command`
- [ ] Output: test files + test execution report (pass/fail)
- [ ] Runs pytest, captures and reports results

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
