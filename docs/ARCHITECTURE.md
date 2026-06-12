# Banviro Architecture

This document describes the system design of Banviro: a personal finance platform with an integrated AI advisor. The application follows a layered architecture with a clear separation between the web client, API, data stores, and AI subsystem.

## Design principles

- **PostgreSQL as the source of truth** for all financial records
- **Self-hosted AI components** (Ollama, Qdrant) for local development and cost control
- **User-scoped data access** at every layer — API, tools, and vector search
- **Explicit orchestration** via LangGraph rather than ad-hoc prompt chains
- **Streaming-first chat** with a synchronous fallback for automation and tests

## System layers

| Layer | Responsibility | Implementation | Status |
| --- | --- | --- | --- |
| Frontend | Authentication UI, dashboards, budgets, AI chat | Next.js 15, React 19, TypeScript | Complete |
| Agent orchestrator | Route intent, invoke tools, retrieve context, generate replies | LangGraph, FastAPI | Complete |
| RAG pipeline | Semantic search over transaction history | Qdrant, Ollama embeddings | Complete |
| LLM | Chat completion and intent routing | Ollama (`llama3.2:3b`, `nomic-embed-text`) | Complete |
| Tool layer | Structured access to finance data | Python MCP-style tools, LLM routing | Partial |
| Data | Persistent application state | PostgreSQL 16 | Complete |
| Deployment | Containers, CI, production hosting | Docker Compose, GitHub Actions | Partial |
| Observability | Tracing and monitoring for AI and API | Phoenix OpenTelemetry | Complete |

The tool layer is **partial** because finance tools are implemented as in-process Python functions rather than a standalone MCP server.

## High-level diagram

```
┌─────────────┐     HTTPS/JWT      ┌─────────────┐
│   Next.js   │ ◄────────────────► │   FastAPI   │
│   Frontend  │                    │     API     │
└─────────────┘                    └──────┬──────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
             ┌────────────┐        ┌────────────┐        ┌────────────┐
             │ PostgreSQL │        │  LangGraph │        │   Qdrant   │
             │  (source   │        │   Agent    │        │  (vectors) │
             │  of truth) │        └─────┬──────┘        └────────────┘
             └────────────┘              │
                                         ▼
                                  ┌────────────┐
                                  │   Ollama   │
                                  │  LLM +     │
                                  │  embeddings│
                                  └────────────┘
```

## AI chat request flow

The primary chat endpoint is `POST /api/v1/ai/chat/stream`. It returns Server-Sent Events with the following sequence: `meta` → `token` (repeated) → `done`.

```
Client (Next.js)
  │
  ▼
POST /api/v1/ai/chat/stream
  │
  ▼
LangGraph agent
  │
  ├─ route_intent      LLM selects finance tools and whether RAG is needed
  │
  ├─ fetch_finance     Execute MCP-style tools against PostgreSQL
  │                      • get_summary
  │                      • list_transactions
  │                      • get_budgets
  │
  ├─ fetch_rag         Query Qdrant when RAG is planned
  │
  └─ generate          Stream completion from Ollama
  │
  ▼
SSE response to client
```

A synchronous endpoint, `POST /api/v1/ai/chat`, is retained for scripts, smoke tests, and integrations that do not require streaming.

## Observability

Phoenix collects OpenTelemetry traces exported from the FastAPI application on startup. Instrumentation covers:

| Component | Span names | Span kind |
| --- | --- | --- |
| Chat request | `ai.chat` | Agent |
| LangGraph nodes | `agent.route_intent`, `agent.fetch_finance`, `agent.fetch_rag`, `agent.generate` | Chain, Tool, Retriever, Agent |
| Ollama | `ollama.generate`, `ollama.generate_stream`, `ollama.embed` | LLM |
| Qdrant | `qdrant.search`, `qdrant.upsert` | Retriever |
| LangGraph runtime | Auto-instrumented via OpenInference LangChain | Agent |

Chat requests attach session metadata (`user_id`, locale, message length) using Phoenix context helpers.

Configuration:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PHOENIX_ENABLED` | `true` | Toggle trace export |
| `PHOENIX_PROJECT_NAME` | `banviro` | Project name in the Phoenix UI |
| `PHOENIX_COLLECTOR_ENDPOINT` | `http://localhost:4317` | OTLP collector (gRPC) |
| `PHOENIX_COLLECTOR_PROTOCOL` | `grpc` | OTLP transport (`grpc` or `http/protobuf`) |
| `PHOENIX_ENDPOINT` | `http://localhost:6006` | Phoenix UI (traces dashboard) |

Set `PHOENIX_ENABLED=false` in tests or CI when Phoenix is not available.

### Intent routing

The `route_intent` node sends the user message to Ollama with a structured JSON schema. The model returns which finance tools to invoke and whether semantic retrieval is required. If Ollama is unavailable or returns invalid JSON, the agent falls back to keyword-based heuristics.

### Prompt constraints

The generation step receives structured context sections (summary, recent transactions, budgets, RAG snippets) and is instructed to:

- Use only figures explicitly present in the context
- Avoid inventing or recalculating amounts
- State clearly when requested data is missing

## Transaction indexing

Transaction records are indexed into Qdrant to support semantic search during RAG retrieval. Indexing runs asynchronously and does not block API responses.

| Trigger | Action |
| --- | --- |
| Transaction created | Upsert vector point |
| Transaction updated | Upsert vector point |
| Transaction deleted | Delete vector point |
| Manual reindex | `POST /api/v1/ai/reindex` rebuilds all points for the authenticated user |

Each indexed document includes the transaction date, type, category, amount, and description. Embeddings are generated via Ollama and stored with a `user_id` payload for tenant isolation.

## Data stores

| Store | Role |
| --- | --- |
| PostgreSQL | Authoritative storage for users, categories, transactions, and budgets |
| Qdrant | Vector index for transaction search and RAG context retrieval |
| Ollama | Model runtime for chat completion, intent routing, and embeddings |

Planned additions:

| Store | Role |
| --- | --- |
| Supabase | Managed PostgreSQL for production deployments |
| DuckDB | Local analytics and export workloads |

## Infrastructure

### Core services

```bash
docker compose up -d
```

Starts PostgreSQL and other core dependencies defined in `docker-compose.yml`.

### AI services

```bash
docker compose -f docker-compose.yml -f docker-compose.ai.yml up -d
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

Provisions Ollama, Qdrant, and Phoenix. On macOS, running Ollama natively (`brew install ollama`) is recommended while keeping Qdrant in Docker.

| Service | Port | Purpose |
| --- | --- | --- |
| Ollama | 11434 | LLM inference and embeddings |
| Qdrant | 6333 | Vector storage and search |
| Phoenix | 6006 | AI observability UI |
| FastAPI | 8000 | REST API |

## Security model

- All `/finance/*` and `/ai/*` routes require a valid JWT access token.
- Finance tools query the database scoped to the authenticated `user_id`.
- Qdrant searches include a mandatory filter on `user_id` in the point payload.
- Credentials, tokens, and secrets are never passed to the LLM.
- Secrets are loaded from environment variables or CI secret stores, not committed to the repository.

## Verification

Run the backend unit tests:

```bash
cd backend && pytest
```

Run the AI smoke test (requires API, Ollama, and Qdrant):

```bash
chmod +x scripts/e2e-ai.sh
./scripts/e2e-ai.sh
```

## Roadmap

**Completed**

- Core API, frontend, and CI pipeline
- Finance CRUD, budgets, analytics, and month filtering
- LangGraph agent with tool invocation and RAG retrieval
- Streaming chat UI in the dashboard
- Transaction indexing on create, update, and delete
- LLM-based intent routing with keyword fallback
- Phoenix OpenTelemetry instrumentation (agent, Ollama, Qdrant)

**Planned**

- Standalone MCP protocol server (FastMCP)
- Production deployment (Vercel, Fly.io or Railway, Supabase)
- Subscription billing and multi-factor authentication
