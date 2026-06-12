# Banviro

Personal finance platform with multi-user accounts, budgeting, analytics, and an integrated AI advisor.

## Overview

Banviro helps users track income and expenses, monitor budgets by category, and explore trends through interactive dashboards. The AI layer answers finance questions using live account data and semantic search over transaction history.

**Core capabilities**

- JWT-authenticated accounts with refresh tokens
- Transaction and category management
- Monthly budgets with progress tracking
- Analytics: balance, spending breakdown, monthly and balance trends
- AI chat with LangGraph orchestration, finance tools, Qdrant RAG, and SSE streaming

## Technology

| Layer | Stack |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Authentication | JWT, bcrypt |
| AI orchestration | LangGraph |
| LLM & embeddings | Ollama |
| Vector store | Qdrant |
| Observability | Phoenix OpenTelemetry (LangGraph, Ollama, Qdrant spans) |
| CI | GitHub Actions |
| Containers | Docker Compose |

For a detailed architecture breakdown, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

```
banviro/
├── backend/              # FastAPI application
├── frontend/             # Next.js web application
├── docs/                 # Architecture and design notes
├── scripts/              # Operational and test scripts
├── docker-compose.yml    # Core services
└── docker-compose.ai.yml # AI services (Ollama, Qdrant, Phoenix)
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose
- [Ollama](https://ollama.com/) (native install or via Docker)

## Getting started

### 1. Database

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

API documentation: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Application: http://localhost:3000

### 4. AI services

Pull the required models:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

**Native Ollama (recommended on macOS)**

```bash
brew install ollama
ollama serve
```

**Docker**

```bash
docker compose -f docker-compose.yml -f docker-compose.ai.yml up -d
docker exec -it banviro-ollama ollama pull llama3.2:3b
docker exec -it banviro-ollama ollama pull nomic-embed-text
```

| Service | Endpoint |
| --- | --- |
| Ollama | http://localhost:11434 |
| Qdrant | http://localhost:6333 |
| Phoenix | http://localhost:6006 |
| AI status | http://localhost:8000/api/v1/ai/status |

Set `AI_ENABLED=true` in `backend/.env` to enable AI features.

Ensure Phoenix is running to collect traces (`docker compose -f docker-compose.yml -f docker-compose.ai.yml up -d phoenix`). Traces appear at http://localhost:6006 under the **banviro** project → **Tracing** tab. Send a chat message first, then refresh the trace list.

## Testing

Run the backend test suite:

```bash
cd backend
pytest
```

Run the AI smoke test (requires API, Ollama, and Qdrant):

```bash
chmod +x scripts/e2e-ai.sh
./scripts/e2e-ai.sh
```

CI runs on every push and pull request to `main` and `develop`.

## API reference

Base path: `/api/v1`

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Service health check |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Authenticate and receive tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user profile |
| GET | `/finance/categories` | List categories |
| GET, POST | `/finance/transactions` | List or create transactions |
| PUT | `/finance/transactions/{id}` | Update a transaction |
| DELETE | `/finance/transactions/{id}` | Delete a transaction |
| GET | `/finance/analytics/summary` | Balance and monthly summary |
| GET | `/finance/analytics/spending-by-category` | Spending by category |
| GET | `/finance/analytics/monthly-trend` | Monthly income and expenses |
| GET | `/finance/analytics/balance-trend` | Balance over time |
| GET, PUT, DELETE | `/finance/budgets` | Manage monthly budgets |
| GET | `/ai/status` | AI subsystem health |
| POST | `/ai/chat` | AI chat (synchronous) |
| POST | `/ai/chat/stream` | AI chat (Server-Sent Events) |
| POST | `/ai/reindex` | Rebuild Qdrant index for the current user |

All finance and AI routes require a valid Bearer token.

## Configuration

**Backend** — `backend/.env`

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `CORS_ORIGINS` | Allowed frontend origins |
| `OLLAMA_MODEL` | Chat model (default: `llama3.2:3b`) |
| `OLLAMA_EMBED_MODEL` | Embedding model (default: `nomic-embed-text`) |
| `QDRANT_URL` | Qdrant base URL |
| `AI_ENABLED` | Enable or disable AI features |
| `PHOENIX_ENABLED` | Enable OpenTelemetry export to Phoenix |
| `PHOENIX_PROJECT_NAME` | Phoenix project name (default: `banviro`) |
| `PHOENIX_COLLECTOR_ENDPOINT` | OTLP collector URL (default: `http://localhost:4317`) |
| `PHOENIX_COLLECTOR_PROTOCOL` | OTLP protocol: `grpc` or `http/protobuf` |

**Frontend** — `frontend/.env.local`

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Backend API URL |

## Roadmap

- [x] Finance CRUD, budgets, and analytics
- [x] LangGraph agent with finance tools and Qdrant RAG
- [x] Streaming AI chat in the dashboard
- [x] Phoenix OpenTelemetry instrumentation
- [ ] MCP protocol server
- [ ] Production deployment pipeline
- [ ] Subscriptions and enhanced security (MFA)

## License

Proprietary. All rights reserved.
