# Banviro — production deployment

This guide covers the GitHub Actions CD pipeline and how to wire Banviro to managed hosting.

## Architecture (recommended)

| Component | Platform | Notes |
| --- | --- | --- |
| Frontend (Next.js) | [Vercel](https://vercel.com) | Static/SSR, global CDN |
| Backend (FastAPI) | [Railway](https://railway.app) or any Docker host | Pulls image from GHCR |
| Database | Railway Postgres or [Supabase](https://supabase.com) | PostgreSQL 16 |
| AI (optional) | Ollama + Qdrant on a VPS or skip in v1 | Not required for core finance |

## CI / CD flow

```
push/PR → CI (test + build) → on main success → Deploy workflow
```

- **CI** (`.github/workflows/ci.yml`) — tests backend, lints/builds frontend on `main` and `develop`.
- **Deploy** (`.github/workflows/deploy.yml`) — runs after CI passes on `main`, or manually via **Actions → Deploy → Run workflow**.

Deploy always:

1. Builds the backend Docker image
2. Pushes to **GitHub Container Registry** (`ghcr.io/<owner>/banviro-api`)

Optional steps (controlled by repository **variables**):

| Variable | Value | Also requires secrets |
| --- | --- | --- |
| `ENABLE_VERCEL_DEPLOY` | `true` | `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` |
| `ENABLE_RAILWAY_DEPLOY` | `true` | `RAILWAY_TOKEN` |
| `RAILWAY_SERVICE_NAME` | e.g. `banviro-api` | (optional, defaults to `banviro-api`) |

## One-time setup

### 1. GitHub Environments

1. Repo → **Settings → Environments** → create `production`
2. (Optional) Add required reviewers or branch protection

### 2. Database (Railway Postgres example)

1. Create a Railway project → **Add PostgreSQL**
2. Copy the `DATABASE_URL` (use the **public** URL if backend runs outside Railway private network)
3. You will set this on the backend service

### 3. Backend on Railway

1. **New service → Deploy from GitHub** or **Empty service**
2. Settings → **Source**: deploy from container registry:
   - Image: `ghcr.io/<your-github-user>/banviro-api:latest`
   - Enable GHCR access (GitHub token or make package public)
3. **Variables** (environment):

| Variable | Example |
| --- | --- |
| `DATABASE_URL` | `postgresql://...` |
| `SECRET_KEY` | long random string |
| `CORS_ORIGINS` | `https://your-app.vercel.app` |
| `ENVIRONMENT` | `production` |
| `AI_ENABLED` | `false` (until Ollama/Qdrant are hosted) |
| `SALTEDGE_APP_ID` | From Salt Edge dashboard |
| `SALTEDGE_SECRET` | From Salt Edge dashboard |
| `SALTEDGE_RETURN_TO_URL` | `https://your-app.vercel.app/integrations/revolut/complete` |

See **[docs/REVOLUT_SALTEDGE.md](REVOLUT_SALTEDGE.md)** for Open Banking setup and troubleshooting.

4. Railway sets `PORT` automatically — the Docker entrypoint uses it.

5. Make GHCR package visible to Railway:
   - GitHub → **Packages** → `banviro-api` → **Package settings** → visibility / access

6. Set repo variable `ENABLE_RAILWAY_DEPLOY=true` and secret `RAILWAY_TOKEN` (Railway → Account → Tokens).

### 4. Frontend on Vercel

1. Import the GitHub repo in Vercel
2. **Root directory**: `frontend`
3. **Environment variable** (production):

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://your-api.railway.app` |

4. Vercel → **Settings → General** → copy **Project ID** and **Org ID**
5. Create a [Vercel token](https://vercel.com/account/settings/tokens)
6. GitHub secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
7. Repo variable: `ENABLE_VERCEL_DEPLOY=true`

Alternatively, skip GitHub deploy for frontend and let Vercel’s native Git integration deploy on push (disable `ENABLE_VERCEL_DEPLOY`).

### 5. CORS

Ensure `CORS_ORIGINS` on the backend includes your Vercel URL (no trailing slash):

```
CORS_ORIGINS=https://banviro.vercel.app
```

## Manual / VPS deploy (Docker Compose)

On a server with Docker:

```bash
cp backend/.env.example backend/.env
# edit .env and set POSTGRES_PASSWORD, SECRET_KEY, etc.

export POSTGRES_PASSWORD=your-secure-password
docker compose -f docker-compose.prod.yml up -d --build
```

Or pull the CI-built image:

```bash
docker pull ghcr.io/<owner>/banviro-api:latest
# run with DATABASE_URL, SECRET_KEY, CORS_ORIGINS, PORT=8000
```

## Migrations

The production Docker image runs `alembic upgrade head` on container start (`docker-entrypoint.sh`). No separate migration step is required for Railway/Docker deploys.

## Smoke test after deploy

```bash
curl https://your-api.example.com/api/v1/health
```

Register/login via the Vercel frontend URL and confirm dashboard loads.

## Troubleshooting

| Issue | Check |
| --- | --- |
| Deploy workflow skipped | CI failed on `main`, or not on `main` branch |
| Railway 502 | `DATABASE_URL`, migrations, `SECRET_KEY` set? |
| Frontend can’t reach API | `NEXT_PUBLIC_API_URL`, CORS, HTTPS |
| GHCR pull denied | Package permissions / public visibility |
| AI offline in prod | Expected if `AI_ENABLED=false` or Ollama not hosted |
| Revolut connect fails | `SALTEDGE_*` vars set? Migrations 006–007 applied? See [REVOLUT_SALTEDGE.md](REVOLUT_SALTEDGE.md) |

## Security checklist

- [ ] Strong `SECRET_KEY` and `POSTGRES_PASSWORD`
- [ ] `ENVIRONMENT=production`
- [ ] CORS limited to your frontend origin
- [ ] GitHub secrets never committed
- [ ] Database not exposed publicly without SSL/firewall
