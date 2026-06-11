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

## Project structure

```
banviro/
├── backend/          # FastAPI API
├── frontend/         # Next.js web app
├── docker-compose.yml
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
- [ ] Chatbot AI advisor (RAG)
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
