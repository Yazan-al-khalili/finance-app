# Finance App — Project Context for Claude

## What this app is
Personal finance tracker. Fetches real SEB Sweden transactions via Enable Banking API and displays them as income/expenses, organized by month and category.

## Stack
- **Backend**: FastAPI + SQLite (`backend/finance.db`) + SQLAlchemy
- **Frontend**: Vue 3 + Vite + Tailwind CSS + Chart.js
- **Bank integration**: Enable Banking REST API (JWT auth, no SDK)

## How to run

```bash
# Terminal 1 — backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev

# Terminal 3 — HTTPS tunnel (required for SEB auth — see redirect URL section below)
npx localtunnel --port 8000
```

## Key files
| File | Purpose |
|---|---|
| `backend/enablebanking.py` | All Enable Banking API calls (JWT signing, list banks, start auth, exchange code, fetch balances/transactions) |
| `backend/main.py` | FastAPI routes — CRUD, auth flow, sync endpoint |
| `backend/models.py` | SQLAlchemy models: `Transaction`, `BankSession` |
| `backend/.env` | `ENABLEBANKING_APP_ID=13ff9c3b-e665-4376-8f86-08456eb03711` |
| `backend/certificate.pem` | Private key for signing JWTs — **never commit** |
| `frontend/src/views/Dashboard.vue` | Landing page: month selector cards + charts + transaction list |
| `frontend/src/views/Transactions.vue` | Full transaction list grouped by month → category |

## Enable Banking — Production app
- **App ID**: `13ff9c3b-e665-4376-8f86-08456eb03711`
- **Environment**: PRODUCTION
- **Service**: Account Information (Restricted — only the 4 linked SEB accounts below)
- **Linked SEB accounts (real IBANs)**:
  - SE7350000000057090081788
  - SE8250000000057093373127
  - SE7250000000052293387380
  - SE4850000000052670280730
- **Data protection email**: Yazankhalili77@gmail.com

## ⚠️ The redirect URL problem — read this every session

SEB requires HTTPS for the OAuth callback. The app runs locally (HTTP), so we use **localtunnel** to get a temporary HTTPS URL.

**The localtunnel URL changes every time you restart it.** This means:

### Every new working session, you must:

1. Start localtunnel:
   ```bash
   npx localtunnel --port 8000
   ```
   It prints something like: `your url is: https://some-words-here.loca.lt`

2. Update `REDIRECT_URL` in `backend/main.py` (line ~28):
   ```python
   REDIRECT_URL = "https://YOUR-NEW-URL.loca.lt/auth/callback"
   ```

3. Update the redirect URL in the **Enable Banking Control Panel**:
   - Go to enablebanking.com → your app → edit redirect URLs
   - Replace the old URL with: `https://YOUR-NEW-URL.loca.lt/auth/callback`

4. Restart the backend so it picks up the new URL.

> **Important**: Once the bank session is connected (account UIDs are stored in `BankSession` table), you can **sync without localtunnel**. Localtunnel is only needed for the initial `/auth/link` → SEB BankID → `/auth/callback` flow. If you're just syncing existing sessions, no tunnel needed.

## Auth flow (how the SEB connection works)
1. User clicks "Connect SEB" → frontend calls `GET /auth/link?country=SE&bank_name=SEB`
2. Backend calls Enable Banking `POST /auth` → gets a SEB BankID login URL
3. User is redirected to SEB's BankID page → authenticates with their phone
4. SEB redirects to `https://YOUR-TUNNEL.loca.lt/auth/callback?code=<one-time-code>`
5. Backend exchanges code via `POST /sessions` → gets account UIDs
6. UIDs stored in `BankSession` table → redirect to `http://localhost:5173/?sync=success`
7. User clicks "Sync Transactions" → `POST /transactions/sync` → fetches and stores transactions

## Transaction classification logic
Enable Banking returns `credit_debit_indicator`: `"CRDT"` (income) or `"DBIT"` (expense).
SEB sometimes omits this for foreign card purchases → we **default to expense** when indicator is missing.
Rule in `main.py`: only `income` if `indicator == "CRDT"` AND `amount > 0`. Everything else → expense.

## Remaining work / ideas
- To be continued next session
