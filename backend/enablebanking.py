"""
Enable Banking integration module
==================================
This module handles all communication with the Enable Banking REST API.

How Enable Banking authentication works (the short version):
  - Enable Banking uses JWT tokens signed with YOUR private key (certificate.pem).
  - You sign a JWT, include it as a Bearer token in every request.
  - Enable Banking verifies the signature using the public key you uploaded
    when you registered the application in their Control Panel.
  - This is called "application-level authentication" — it proves requests
    are coming from your registered app.

The banking authorization flow (OAuth2-like, one-time per user):
  Step 1  ─  Call POST /auth  →  get a bank login URL
  Step 2  ─  Redirect the user to that URL  →  they log in inside their bank
  Step 3  ─  Bank redirects back to your callback URL with ?code=<one-time-code>
  Step 4  ─  Call POST /sessions with that code  →  get a session + account UIDs
  Step 5  ─  Use account UIDs to fetch balances and transactions any time

After Step 4, the session is valid for the duration you set in `valid_until`
(up to 90 days for most banks). You do NOT need to repeat the bank login.
"""

import os
import jwt          # PyJWT — signs and encodes the JWT
import requests     # standard HTTP client
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# ── Load environment variables from .env ──────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Configuration ─────────────────────────────────────────────────────────────
APP_ID   = os.getenv("ENABLEBANKING_APP_ID")
API_BASE = "https://api.enablebanking.com"

# Private key: prefer the env var (base64-encoded) used in production,
# fall back to the local certificate.pem file for local development.
def _load_private_key() -> bytes:
    b64 = os.getenv("CERT_PRIVATE_KEY_B64")
    if b64:
        import base64
        return base64.b64decode(b64)
    cert_path = os.path.join(os.path.dirname(__file__), "certificate.pem")
    if os.path.exists(cert_path):
        return open(cert_path, "rb").read()
    raise RuntimeError(
        "No private key found. Set CERT_PRIVATE_KEY_B64 env var "
        "or place certificate.pem in the backend directory."
    )


# ── Internal helper: build the signed JWT and return auth headers ──────────────
def _auth_headers() -> dict:
    """
    Build a fresh, signed JWT and return it as an Authorization header dict.

    WHY a new JWT on every call?
    JWT tokens expire (we set exp = now + 1 hour). Re-creating them on each
    request is the simplest approach — it avoids caching stale tokens.

    WHAT goes in the JWT?
      iss / aud  → fixed strings required by Enable Banking
      iat        → "issued at" — current Unix timestamp
      exp        → "expires at" — 1 hour from now
      kid        → "key ID" in the HEADER (not payload) — your App ID,
                   so Enable Banking knows which public key to verify with
    """
    if not APP_ID:
        raise RuntimeError("ENABLEBANKING_APP_ID is not set")

    private_key = _load_private_key()

    now = int(datetime.now(timezone.utc).timestamp())

    payload = {
        "iss": "enablebanking.com",      # Issuer — fixed value required by the API
        "aud": "api.enablebanking.com",  # Audience — fixed value required by the API
        "iat": now,                      # Issued at (Unix timestamp)
        "exp": now + 3600,               # Expires 1 hour from now
    }

    # jwt.encode() returns a string. The `headers` kwarg adds extra fields to
    # the JWT header (the part before the first dot in the token string).
    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",              # RSA + SHA-256 — what Enable Banking expects
        headers={"kid": APP_ID},        # Tells Enable Banking which app this is
    )

    return {"Authorization": f"Bearer {token}"}


# ── Step 1: List banks (ASPSPs) available in a country ────────────────────────
def list_banks(country: str = "SE") -> list[dict]:
    """
    Return all banks that Enable Banking supports in `country`.

    `country` is a 2-letter ISO code, e.g. "SE" for Sweden.

    Each bank dict looks like:
        {"name": "SEB", "country": "SE", "logo": "...", ...}

    You need the bank's "name" and "country" to start an auth session.
    """
    resp = requests.get(
        f"{API_BASE}/aspsps",
        params={"country": country},
        headers=_auth_headers(),
    )
    resp.raise_for_status()  # raises an exception for 4xx/5xx responses
    return resp.json().get("aspsps", [])


# ── Step 2: Start the authorization flow ──────────────────────────────────────
def start_auth(
    bank_name: str,
    country: str,
    redirect_url: str,
    state: str,
    psu_type: str = "personal",
    valid_days: int = 90,
) -> str:
    """
    Ask Enable Banking to begin an authorization session for `bank_name`.

    Returns a URL (string) that you MUST redirect the user to. That URL
    opens the bank's own login page (e.g., SEB's BankID flow in Sweden).

    After the user authenticates:
      → The bank redirects them to `redirect_url?code=<code>&state=<state>`
      → You then call `exchange_code_for_session(code)` with that code.

    Parameters:
      bank_name    Name as returned by list_banks(), e.g. "SEB"
      country      ISO-2 country code, e.g. "SE"
      redirect_url Your callback endpoint, e.g. "http://localhost:8000/auth/callback"
      state        A random UUID you generate; returned unchanged in the callback
                   so you can verify the response isn't forged
      psu_type     "personal" for retail accounts, "business" for corporate
      valid_days   How many days you want access to the account data (max 90)
    """
    valid_until = (datetime.now(timezone.utc) + timedelta(days=valid_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    body = {
        "access": {
            "valid_until": valid_until,   # How long Enable Banking should allow data access
        },
        "aspsp": {
            "name": bank_name,            # e.g. "SEB"
            "country": country,           # e.g. "SE"
        },
        "state": state,                   # Your random UUID — returned in callback for CSRF protection
        "redirect_url": redirect_url,     # Where the bank sends the user after login
        "psu_type": psu_type,             # "personal" or "business"
    }

    resp = requests.post(f"{API_BASE}/auth", json=body, headers=_auth_headers())
    if not resp.ok:
        print(f"Enable Banking /auth error {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json()["url"]


# ── Step 3: Exchange the callback code for a session ──────────────────────────
def exchange_code_for_session(code: str) -> dict:
    """
    After the user authenticates in their bank, Enable Banking calls your
    redirect_url with a one-time `code` query parameter.

    Pass that code here to create a persistent session.

    Returns a dict that includes:
      session_id  — store this; you'll need it if you want to delete the session later
      accounts    — list of account dicts, each with a "uid" you use for data fetches
      aspsp       — the bank that was connected

    Example response shape:
      {
        "session_id": "abc-123",
        "accounts": [
          {"uid": "uid-xyz", "account_id": {"iban": "SE..."}, ...}
        ],
        "aspsp": {"name": "SEB", "country": "SE"}
      }
    """
    resp = requests.post(
        f"{API_BASE}/sessions",
        json={"code": code},
        headers=_auth_headers(),
    )
    resp.raise_for_status()
    return resp.json()


# ── Step 4a: Fetch balances for one account ────────────────────────────────────
def get_balances(account_uid: str) -> list[dict]:
    """
    Fetch current balance(s) for the account identified by `account_uid`.

    Returns a list (banks often report multiple balance types, e.g.
    "closingBooked" and "expected"). Each dict looks like:
      {
        "balance_amount": {"amount": "1234.56", "currency": "SEK"},
        "balance_type": "closingBooked",
        "last_change_date_time": "2024-01-15T10:30:00Z"
      }
    """
    resp = requests.get(
        f"{API_BASE}/accounts/{account_uid}/balances",
        headers=_auth_headers(),
    )
    resp.raise_for_status()
    return resp.json().get("balances", [])


# ── Step 4b: Fetch transactions for one account ────────────────────────────────
def get_transactions(
    account_uid: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """
    Fetch booked transactions for `account_uid`.

    Optional date filtering:
      date_from / date_to should be "YYYY-MM-DD" strings.
      If omitted, the bank decides how far back to go (often 90 days).

    Each transaction dict contains fields like:
      booking_date            "2024-01-15"
      transaction_amount      {"amount": "-250.00", "currency": "SEK"}
      credit_debit_indicator  "DBIT" (debit/expense) or "CRDT" (credit/income)
      entry_reference         unique reference for deduplication
      creditor.name           merchant name (if available)
      remittance_information  list of description strings
    """
    params: dict = {}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    resp = requests.get(
        f"{API_BASE}/accounts/{account_uid}/transactions",
        params=params,
        headers=_auth_headers(),
    )
    resp.raise_for_status()
    return resp.json().get("transactions", [])
