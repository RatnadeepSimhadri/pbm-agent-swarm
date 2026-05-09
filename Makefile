.PHONY: dev seed-backend seed-frontend seed-db test clean

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

# Clean generated files
clean:
	rm -f seed-app/backend/pbm.db
	rm -rf seed-app/backend/.venv
	rm -rf seed-app/frontend/node_modules
