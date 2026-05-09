# PBM Platform — Seed Application

A Pharmacy Benefit Management (PBM) web application for members to view their plan coverage, formulary, and medication information.

## Quick Start

```bash
# From repo root
make install   # Install all dependencies
make dev       # Start backend (:8000) + frontend (:5173)
```

## Architecture

```
seed-app/
├── backend/             # FastAPI + SQLAlchemy + SQLite
│   └── app/
│       ├── main.py      # App entry point, router registration
│       ├── config.py    # Settings (env vars with PBM_ prefix)
│       ├── database.py  # Engine, session factory, Base model
│       ├── auth.py      # JWT token creation/validation, get_current_member
│       ├── seed.py      # Database seeding script
│       ├── models/      # SQLAlchemy ORM models
│       ├── schemas/     # Pydantic v2 request/response schemas
│       ├── services/    # Business logic layer
│       └── routes/      # FastAPI route handlers (thin)
└── frontend/            # React + Vite + Tailwind
    └── src/
        ├── App.jsx          # React Router configuration
        ├── main.jsx         # Entry point
        ├── index.css        # Tailwind directives + design tokens
        ├── contexts/        # React contexts (AuthContext)
        ├── hooks/           # Custom hooks (useAuth, useApi)
        ├── components/      # Shared layout components
        └── pages/           # Route page components
```

## Backend Patterns

### Adding a New Model

1. Create `app/models/new_entity.py`:
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class NewEntity(Base):
    __tablename__ = "new_entities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
```

2. Export it in `app/models/__init__.py`:
```python
from app.models.new_entity import NewEntity
```

### Adding a New Schema

Create `app/schemas/new_entity.py`:
```python
from pydantic import BaseModel, ConfigDict

class NewEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
```

### Adding a New Service

Create `app/services/new_entity_service.py`:
```python
from sqlalchemy.orm import Session
from app.models.new_entity import NewEntity

def get_new_entity(db: Session, entity_id: int) -> NewEntity | None:
    return db.query(NewEntity).filter(NewEntity.id == entity_id).first()
```

### Adding a New Route

1. Create `app/routes/new_entity.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_member
from app.database import get_db
from app.schemas.new_entity import NewEntityResponse
from app.services.new_entity_service import get_new_entity

router = APIRouter(prefix="/api/new-entities", tags=["new-entities"])

@router.get("/{entity_id}", response_model=NewEntityResponse)
def get_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    _member=Depends(get_current_member),  # Auth required
):
    entity = get_new_entity(db, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Not found")
    return NewEntityResponse.model_validate(entity)
```

2. Register in `app/main.py`:
```python
from app.routes import new_entity
app.include_router(new_entity.router)
```

### Key Conventions

- **Routes are thin**: Only validate input, call a service, return response. No business logic.
- **Services hold business logic**: Each domain entity gets its own service module.
- **Auth dependency**: Use `Depends(get_current_member)` on any endpoint requiring authentication. Use `_member` if you don't need the member object.
- **DB sessions**: Always injected via `Depends(get_db)`, never created manually in routes.
- **SQLAlchemy 2.0 style**: Use `Mapped[]` and `mapped_column()`, not `Column()`.
- **Pydantic v2**: All schemas use `ConfigDict(from_attributes=True)` for ORM compatibility.
- **Naming**: snake_case for Python files and variables. Table names are plural.

## Frontend Patterns

### Adding a New Page

1. Create `src/pages/NewPage.jsx`:
```jsx
import { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';

export function NewPage() {
  const { get } = useApi();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    get('/api/new-entities')
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [get]);

  if (loading) return <div className="animate-pulse">...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">New Page</h1>
      {/* Content */}
    </div>
  );
}
```

2. Add route in `src/App.jsx`:
```jsx
import { NewPage } from './pages/NewPage';
// Inside the protected layout Route:
<Route path="/new-page" element={<NewPage />} />
```

3. Add nav link in `src/components/Sidebar.jsx`:
```jsx
const navItems = [
  // ... existing items
  { to: '/new-page', label: 'New Page', icon: NewPageIcon },
];
```

### Key Conventions

- **`useApi` hook**: Always use this for API calls. It handles auth token injection, error responses, and session expiry.
- **`useAuth` hook**: Access auth state (member, token, login, logout, isAuthenticated).
- **Tailwind only**: No CSS files. All styling via Tailwind utility classes.
- **Design tokens**: Primary (deep blue), Accent (teal), Slate (neutrals). Defined in `index.css` under `@theme`.
- **Component naming**: PascalCase files (`NewPage.jsx`), named exports.
- **Loading states**: Use `animate-pulse` skeleton patterns.
- **Layout**: All authenticated pages render inside `AppLayout` via React Router `<Outlet>`.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | No | Login with email, returns JWT |
| GET | `/api/members/me` | Yes | Current member profile + plan |
| GET | `/api/plans/{id}` | Yes | Plan details with formulary summary |
| GET | `/api/drugs` | Yes | List drugs (query param `q` for search) |
| GET | `/api/drugs/{id}` | Yes | Drug detail |
| GET | `/api/formulary/{plan_id}` | Yes | Formulary with all drug tier/copay data |
| GET | `/api/health` | No | Health check |

## Data Model

- **Member** → belongs to a **Plan**
- **Plan** → has one **Formulary**
- **Formulary** → has many **FormularyDrug** entries
- **FormularyDrug** → links a **Drug** to a Formulary with tier, copay, prior auth, etc.
- **Pharmacy** — retail and mail-order pharmacy locations
- **Prescriber** — healthcare providers with NPI numbers

## Demo Accounts

| Name | Email | Plan |
|------|-------|------|
| Sarah Johnson | sarah.johnson@example.com | Gold |
| Michael Chen | michael.chen@example.com | Gold |
| Emily Rodriguez | emily.rodriguez@example.com | Silver |
| James Wilson | james.wilson@example.com | Silver |
| Priya Patel | priya.patel@example.com | Bronze |
