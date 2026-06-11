# Banviro — Architecture ($0 AI Stack)

Banviro follows a layered architecture inspired by the **$0 AI Architecture Stack (2026)**.
Each layer has a clear role; services run locally via Docker profiles where possible.

## Layer map

| # | Layer | Role in Banviro | Technology |
|---|--------|-----------------|------------|
| 1 | **Frontend** | Dashboard, auth, charts, chat UI (next) | Next.js 15, Vercel (prod) |
| 2 | **Agent Orchestrator** | Routes user questions: SQL vs RAG vs tools | FastAPI + custom orchestrator → LangGraph (phase 2) |
| 3 | **RAG Pipeline** | Semantic search on transaction descriptions | Qdrant (local), embeddings via Ollama |
| 4 | **LLM Layer** | Local inference, $0 | Ollama (Llama 3.2, Mistral, Gemma) |
| 5 | **Tool Use (MCP)** | GitHub, finance DB, exports | MCP-style tool registry in Python |
| 6 | **Code Agent** | Dev automation (optional, dev-only) | Claude Code / Aider (outside runtime) |
| 7 | **Data Layer** | Users, transactions, budgets | PostgreSQL (prod: Supabase free tier) |
| 8 | **Deployment** | CI/CD + containers | Docker, GitHub Actions, Cloudflare (later) |
| — | **Observability** | Traces for AI + API | Phoenix (self-hosted, profile `ai`) |

## Request flow (AI chat)

```
User (Next.js)
    → POST /api/v1/ai/chat
    → Orchestrator
        ├─ needs structured data? → Finance MCP tools → PostgreSQL
        ├─ needs semantic context? → RAG → Qdrant
        └─ generate answer → Ollama LLM
    → Response + optional sources
    → Phoenix traces (when enabled)
```

## Docker profiles

**Core (always):**
```bash
docker compose up -d
# db + api
```

**AI stack ($0 local):**
```bash
docker compose -f docker-compose.yml -f docker-compose.ai.yml up -d
# + ollama, qdrant, phoenix
ollama pull llama3.2
```

## Data strategy

| Store | Use |
|-------|-----|
| **PostgreSQL** | Source of truth — users, transactions, budgets |
| **Qdrant** | Vector index for transaction notes / chat context |
| **DuckDB** | (Phase 3) Local analytics / exports |
| **Supabase** | (Prod) Managed Postgres + auth optional migration |

## Security

- JWT auth on all `/finance/*` and `/ai/*` routes
- LLM never receives raw passwords or tokens
- MCP tools scoped per `user_id` (row-level isolation)
- Secrets via `.env` / GitHub Secrets — never in repo

## Roadmap

- [x] Core API + frontend + CI
- [x] Finance CRUD, charts, budgets, filters
- [x] AI layer scaffold (orchestrator, Ollama, RAG stub, MCP tools)
- [ ] LangGraph agent graph
- [ ] Chat UI in dashboard
- [ ] Transaction indexing into Qdrant
- [ ] Phoenix OpenTelemetry instrumentation
- [ ] Deploy: Vercel (web) + Fly.io/Railway (API) + Supabase (DB)
