.PHONY: dev seed-backend seed-frontend orchestrator dashboard demo seed-db test clean

# Start full stack (backend + frontend concurrently)
dev:
	@echo "Starting PBM Platform..."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@trap 'kill 0' EXIT; \
		(cd seed-app/backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
		(cd seed-app/frontend && npm run dev) & \
		wait

# Start seed app backend on :8000
seed-backend:
	@echo "Starting seed backend on http://localhost:8000..."
	cd seed-app/backend && \
		source .venv/bin/activate && \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start seed app frontend on :5173
seed-frontend:
	@echo "Starting seed frontend on http://localhost:5173..."
	cd seed-app/frontend && npm run dev

# Start orchestrator on :8001
orchestrator:
	@echo "Starting orchestrator on http://localhost:8001..."
	cd orchestrator && \
		source .venv/bin/activate && \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Start dashboard on :5174
dashboard:
	@echo "Starting dashboard on http://localhost:5174..."
	cd dashboard && npm run dev

# Start orchestrator + dashboard for demo (no seed app needed)
demo:
	@echo "Starting Demo..."
	@echo "  Orchestrator: http://localhost:8001"
	@echo "  Dashboard:    http://localhost:5174"
	@trap 'kill 0' EXIT; \
		(cd orchestrator && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001) & \
		(cd dashboard && npm run dev) & \
		wait

# Re-seed the database (delete and recreate)
seed-db:
	cd seed-app/backend && \
		rm -f pbm.db && \
		source .venv/bin/activate && \
		python -c "from app.database import Base, engine, SessionLocal; from app.models import *; from app.seed import seed_database; Base.metadata.create_all(bind=engine); db = SessionLocal(); seed_database(db); db.close(); print('Database seeded.')"

# Run backend tests
test:
	cd seed-app/backend && \
		source .venv/bin/activate && \
		pytest -v

# Install all dependencies
install:
	cd seed-app/backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
	cd seed-app/frontend && npm install
	cd orchestrator && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
	cd dashboard && npm install

# Clean generated files
clean:
	rm -f seed-app/backend/pbm.db
	rm -rf seed-app/backend/.venv
	rm -rf seed-app/frontend/node_modules
	rm -rf orchestrator/.venv
	rm -rf orchestrator/workspaces
	rm -rf dashboard/node_modules
