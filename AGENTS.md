# AGENTS.md

## Project

SupportOps Agent is a full-stack AI customer support operations demo. The repository root contains:

- `backend/`: FastAPI, SQLAlchemy, SQLite, explicit agent workflow, RAG, approvals, evals, pytest tests.
- `frontend/`: React 18, TypeScript, Vite, Tailwind CSS, Recharts dashboard.
- `README.md`: Chinese-first product and run documentation.
- `docker-compose.yml`: local backend/frontend orchestration.

## Backend Commands

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Tests:

```bash
cd backend
pytest -q
```

## Frontend Commands

```bash
cd frontend
npm install
npm run dev
npm run build
```

## Implementation Notes

- Default LLM provider must remain `mock`; the app should run without API keys.
- Never commit secrets, local SQLite databases, virtualenvs, node modules, build output, or server logs.
- Keep safety logic deterministic in Python. Refunds, cancellations, address changes, account deletion, fraud, legal, and hacked-account flows must not execute automatically.
- Keep RAG citations visible in API responses and frontend ticket details.
- Preserve the explicit workflow node names used by tests and README.
- If adding dependencies, update the relevant lockfile or requirements file and rerun tests/build.

## Verification Before Push

Run at minimum:

```bash
cd backend
pytest -q
cd ../frontend
npm run build
```
