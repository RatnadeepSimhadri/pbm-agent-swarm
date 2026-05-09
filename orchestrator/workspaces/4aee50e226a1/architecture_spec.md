# Architecture Specification — Drug Cost Checker

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

## Component Spec — CostCheckerPage
```
┌─────────────────────────────────────────┐
│ Drug Cost Checker                       │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🔍 Search for a medication...       │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Metformin        │ │ Atorvastatin    │ │
│ │ 500mg tablet     │ │ 20mg tablet     │ │
│ │                  │ │                 │ │
│ │ Tier 1 (Generic) │ │ Tier 1 (Generic)│ │
│ │ Copay: $10       │ │ Copay: $10      │ │
│ │                  │ │                 │ │
│ │ No prior auth    │ │ No prior auth   │ │
│ │ Qty limit: 30    │ │ Qty limit: 30   │ │
│ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────┘
```
