# Task Breakdown & Dependency Graph

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
