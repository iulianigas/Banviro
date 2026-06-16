# Revolut integration via Salt Edge (Open Banking)

Banviro imports Revolut transactions for users in Romania using [Salt Edge](https://www.saltedge.com) Account Information Services (AIS). This is the PSD2-compliant path for **Revolut Personal** accounts (no direct Revolut API required).

## Architecture

```
User (browser)
    → Banviro frontend (/integrations/revolut)
    → Banviro API (FastAPI)
    → Salt Edge API v6 (Connect + AIS)
    → Revolut (user consent via Salt Edge widget)
    → Transactions stored in PostgreSQL → dashboard charts
```

| Component | Role |
| --- | --- |
| **Salt Edge Connect** | OAuth-style consent UI; user picks Revolut and authorizes |
| **Banviro backend** | Creates Salt Edge customer, starts connect session, syncs transactions |
| **Banviro DB** | `bank_customers`, `bank_connections`, `transactions.external_id` |

## User flow

1. User logs in and opens **Dashboard → Revolut** (or `/integrations/revolut`).
2. Clicks **Conectează Revolut** → backend returns `connect_url` → browser redirects to Salt Edge.
3. User selects **Revolut** (Romania) and completes consent (SCA).
4. Salt Edge redirects to `SALTEDGE_RETURN_TO_URL` (`/integrations/revolut/complete`).
5. Frontend calls `POST /integrations/revolut/complete` then `POST /integrations/revolut/sync`.
6. Imported transactions appear in the dashboard (category: **Revolut import**).

Manual re-sync: **Sincronizează tranzacțiile** on `/integrations/revolut`.

## API endpoints

Base path: `/api/v1/integrations/revolut` (Bearer token required)

| Method | Path | Description |
| --- | --- | --- |
| POST | `/connect` | Create Salt Edge connect session; returns `{ "connect_url": "..." }` |
| POST | `/complete` | Persist connection after user returns from Salt Edge |
| POST | `/sync` | Import transactions; returns `{ "created": N, "skipped": M }` |

Returns `503` if `SALTEDGE_APP_ID` / `SALTEDGE_SECRET` are not configured.

## Environment variables

**Backend** (`backend/.env` or Railway):

| Variable | Description |
| --- | --- |
| `SALTEDGE_BASE_URL` | Default: `https://www.saltedge.com/api/v6` |
| `SALTEDGE_APP_ID` | App ID from Salt Edge client dashboard |
| `SALTEDGE_SECRET` | Secret from Salt Edge client dashboard |
| `SALTEDGE_RETURN_TO_URL` | Where Salt Edge redirects after consent |

**Examples**

Local:

```
SALTEDGE_RETURN_TO_URL=http://localhost:3000/integrations/revolut/complete
```

Production:

```
SALTEDGE_RETURN_TO_URL=https://banviro.vercel.app/integrations/revolut/complete
```

Never commit real `SALTEDGE_APP_ID` or `SALTEDGE_SECRET` to git.

## Database migrations

Migrations `006` and `007` add:

- `bank_customers` — maps Banviro user → Salt Edge `customer_id`
- `bank_connections` — stores Salt Edge `connection_id` per user/bank
- `transactions.external_id` — deduplicates imported transactions

Production: migrations run automatically via `docker-entrypoint.sh` on deploy. If needed manually:

```bash
alembic upgrade head
```

## Salt Edge account setup

1. Register at [saltedge.com](https://www.saltedge.com) and complete the application form.
2. Describe the product as a **personal finance app (B2C)** in **Romania**, using **AIS only** (read accounts + transactions), starting with **Revolut**.
3. After approval (typically 1–2 business days), copy **App ID** and **Secret** from the client dashboard.
4. **Test / sandbox**: use Salt Edge fake providers to validate the connect + sync flow.
5. **Revolut Romania (real)**: request Test then Live access for the Revolut provider through Salt Edge support.

## Production checklist

- [ ] `SALTEDGE_APP_ID` and `SALTEDGE_SECRET` set on Railway
- [ ] `SALTEDGE_RETURN_TO_URL` points to production frontend `/integrations/revolut/complete`
- [ ] `CORS_ORIGINS` includes your Vercel URL
- [ ] Migrations `006` + `007` applied (`alembic upgrade head`)
- [ ] Frontend deployed with Revolut integration pages
- [ ] End-to-end test: connect → complete → sync → dashboard shows data

## Troubleshooting

| Issue | Check |
| --- | --- |
| `Salt Edge integration is not configured` | `SALTEDGE_APP_ID` / `SALTEDGE_SECRET` missing on backend |
| `No connections found yet` | User did not finish Salt Edge widget; wait and retry `/complete` |
| CORS / fetch errors | `NEXT_PUBLIC_API_URL` uses `https://` and matches Railway domain |
| Duplicate transactions | `external_id` unique per user; re-sync should skip existing rows |
| Revolut not in widget | Salt Edge account may still be sandbox-only; request Revolut RO access |

## Limitations (MVP)

- **Revolut only** (Romania); other banks can be added later via the same Salt Edge flow.
- **Manual sync** by default (no scheduled cron yet).
- Imported transactions use a single category per type: **Revolut import** (no merchant → category mapping yet).
- **AIS only** — no payment initiation (PIS).

## Related files

| Path | Purpose |
| --- | --- |
| `backend/app/integrations/saltedge_client.py` | Salt Edge HTTP client |
| `backend/app/api/routes/revolut.py` | Connect / complete / sync routes |
| `backend/app/models/bank_customer.py` | Salt Edge customer mapping |
| `backend/app/models/bank_connection.py` | Connection storage |
| `frontend/src/app/integrations/revolut/` | Connect UI and callback page |
