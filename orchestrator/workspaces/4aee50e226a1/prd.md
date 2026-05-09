# Product Requirements Document

## Feature: Drug Cost Checker

### Problem Statement
Members currently have no way to check what their medications will cost before filling a prescription. This leads to surprise costs at the pharmacy counter, medication non-adherence due to cost concerns, and increased call center volume for cost inquiries.

### Intent
> Members should be able to check what their medications will cost before filling them

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
