# Banviro

Personal finance tracker — charts, budgets, month filters, and secure multi-user access.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Auth | JWT (access + refresh tokens), bcrypt |
| CI | GitHub Actions |
| AI Orchestrator | FastAPI orchestrator → LangGraph (phase 2) |
| LLM | Ollama (local, $0) |
| RAG | Qdrant (local) |
| Observability | Phoenix (profile `ai`) |
| Deploy | Docker, Vercel/Cloudflare (planned) |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full $0 AI stack mapping.

## Project structure

```
banviro/
├── backend/
│   ├── app/
│   │   ├── ai/           # Orchestrator, LLM, RAG
│   │   ├── mcp/          # MCP-style tools
│   │   └── api/          # REST routes
├── frontend/             # Next.js web app
├── docs/ARCHITECTURE.md
├── docker-compose.yml    # core (db + api)
├── docker-compose.ai.yml # optional AI services
└── .github/workflows/ci.yml
```

## Quick start

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

### 2. Backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

App: http://localhost:3000

### 4. AI stack (optional, $0 local)

**Varianta A — Ollama nativ pe Mac (recomandat, fără Docker profiles):**

```bash
brew install ollama
ollama serve          # Terminal separat, lasă-l pornit
ollama pull llama3.2  # Terminal nou
```

**Varianta B — AI services în Docker (2 fișiere compose):**

```bash
docker compose -f docker-compose.yml -f docker-compose.ai.yml up -d
docker exec -it banviro-ollama ollama pull llama3.2
```

Pe Docker vechi, înlocuiește `docker compose` cu `docker-compose`.

- Ollama: http://localhost:11434
- Qdrant: http://localhost:6333
- Phoenix: http://localhost:6006
- AI status: http://localhost:8000/api/v1/ai/status
- Chat: `POST /api/v1/ai/chat` `{ "message": "..." }` (Bearer token)

## API endpoints (v1)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login (returns JWT tokens) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Current user (requires Bearer token) |
| GET | `/api/v1/finance/categories` | List categories |
| GET/POST | `/api/v1/finance/transactions` | List / create transactions |
| DELETE | `/api/v1/finance/transactions/{id}` | Delete transaction |
| GET | `/api/v1/finance/analytics/summary` | Balance & monthly stats |
| GET | `/api/v1/finance/analytics/spending-by-category` | Pie chart data |
| GET | `/api/v1/finance/analytics/monthly-trend` | Bar chart data (6 months) |
| GET | `/api/v1/finance/analytics/balance-trend` | Balance evolution (6 months) |
| GET/PUT/DELETE | `/api/v1/finance/budgets` | Monthly budgets per category |
| GET | `/api/v1/ai/status` | AI layer health |
| POST | `/api/v1/ai/chat` | Finance AI advisor |

## GitHub setup

1. Create a new repository on GitHub (e.g. `banviro`).
2. Push this project:

```bash
git add .
git commit -m "Initial Banviro project"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/banviro.git
git push -u origin main
```

3. Every push/PR to `main` or `develop` triggers CI (tests + build).
4. Deploy step is a placeholder — configure Railway/Fly.io/Vercel in the next phase.

## Next phases

- [x] Transactions & categories (CRUD)
- [x] Charts & dashboard metrics
- [x] Month filter + balance trend + budgets
- [x] AI layer scaffold (Ollama + Qdrant + orchestrator)
- [ ] Chat UI in dashboard
- [ ] LangGraph agent + Qdrant indexing
- [ ] Stripe subscriptions
- [ ] Production deploy pipeline
- [ ] MFA & enhanced security hardening

## Environment variables

**Backend** (`backend/.env`):

- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing key (use a long random value in production)
- `CORS_ORIGINS` — Allowed frontend origins

**Frontend** (`frontend/.env.local`):

- `NEXT_PUBLIC_API_URL` — Backend API URL

## License

Private — all rights reserved.
