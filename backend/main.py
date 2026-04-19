import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import models
import database
from pydantic import BaseModel
from datetime import date as date_type, datetime
import uuid

import enablebanking  # our module in backend/enablebanking.py
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Create database tables on startup (safe to call repeatedly)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set these in Railway (production) or .env (local dev).
# REDIRECT_URL  — the /auth/callback URL the bank redirects to after BankID
# FRONTEND_URL  — where to send the user after auth completes
REDIRECT_URL  = os.getenv("REDIRECT_URL",  "http://localhost:8000/auth/callback")
FRONTEND_URL  = os.getenv("FRONTEND_URL",  "http://localhost:5173")


# ── Database session dependency ────────────────────────────────────────────────
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Pydantic schemas ───────────────────────────────────────────────────────────
class TransactionBase(BaseModel):
    type: str
    category: str
    amount: float
    date: date_type
    note: str = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    external_id: str = None

    class Config:
        orm_mode = True


# ── Manual transaction CRUD ────────────────────────────────────────────────────

@app.get("/transactions", response_model=List[Transaction])
def get_transactions(db: Session = Depends(get_db)):
    try:
        return db.query(models.Transaction).order_by(models.Transaction.date.desc()).all()
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        models.Base.metadata.create_all(bind=database.engine)
        return []

@app.post("/transactions", response_model=Transaction)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.delete("/transactions/all")
def clear_all_transactions(db: Session = Depends(get_db)):
    count = db.query(models.Transaction).count()
    db.query(models.Transaction).delete()
    db.commit()
    return {"deleted": count}

@app.delete("/transactions/{id}")
def delete_transaction(id: int, db: Session = Depends(get_db)):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_transaction)
    db.commit()
    return {"message": "Deleted"}


# ── Enable Banking: authorization flow ────────────────────────────────────────

@app.get("/auth/link")
def link_bank(country: str = "SE", bank_name: str = "SEB"):
    """
    Step 1 of the bank connection flow.

    Returns {"url": "<bank login URL>"}.
    The frontend should redirect the user to that URL (or open it in a new tab).
    After the user authenticates, the bank calls /auth/callback automatically.
    """
    try:
        # Fetch all banks available in `country`
        banks = enablebanking.list_banks(country=country)

        # Find the requested bank by name (case-insensitive substring match)
        target = next(
            (b for b in banks if bank_name.upper() in b["name"].upper()), None
        )

        # Fallback: use the Mock ASPSP for sandbox testing
        if not target:
            print(f"DEBUG: '{bank_name}' not found. Falling back to Mock ASPSP.")
            target = next(
                (b for b in banks if "MOCK" in b["name"].upper()), None
            )

        if not target:
            available = [b["name"] for b in banks[:10]]
            raise HTTPException(
                status_code=404,
                detail=f"Bank '{bank_name}' not found in {country}. Available: {available}",
            )

        print(f"DEBUG: Starting auth for {target['name']} ({target['country']})")

        # state is a random UUID — the bank echoes it back in the callback URL
        # so you can verify the response hasn't been tampered with (CSRF protection)
        state = str(uuid.uuid4())

        auth_url = enablebanking.start_auth(
            bank_name=target["name"],
            country=target["country"],
            redirect_url=REDIRECT_URL,
            state=state,
        )
        return {"url": auth_url}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in link_bank: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/callback")
def auth_callback(
    state: str,
    code: str = None,
    error: str = None,
    db: Session = Depends(get_db),
):
    """
    Step 2: Enable Banking redirects here after the user authenticates.

    Enable Banking may call this with either:
      ?code=<token>          — success, exchange for a session
      ?error=<reason>        — user cancelled or something went wrong
    Both cases must be handled; FastAPI returns 422 if a required param is missing.
    """
    if error:
        print(f"Auth error from Enable Banking: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/?auth_error={error}")

    if not code:
        return RedirectResponse(url=f"{FRONTEND_URL}/?auth_error=no_code")

    # Exchange the one-time code for a session with account access
    session = enablebanking.exchange_code_for_session(code)
    print(f"DEBUG session response: {session}")  # temporary — remove once confirmed working

    # Filter out any accounts where uid is None before joining
    account_uids = ",".join([
        acc["uid"] for acc in session.get("accounts", [])
        if acc.get("uid") is not None
    ])

    bank_session = models.BankSession(
        aspsp_id=session.get("aspsp", {}).get("name", "unknown"),
        session_id=session["session_id"],
        token=account_uids,  # Reusing `token` column to store UIDs (comma-separated)
    )
    db.add(bank_session)
    db.commit()

    # Redirect back to the frontend; the ?sync=success tells it to show a success message
    return RedirectResponse(url=f"{FRONTEND_URL}/?sync=success")


# ── Enable Banking: data fetching ─────────────────────────────────────────────

@app.get("/balances")
def get_balances(db: Session = Depends(get_db)):
    """
    Return current balances for all linked accounts.

    Calls Enable Banking's /accounts/{uid}/balances for each stored account.
    """
    bank_session = (
        db.query(models.BankSession)
        .order_by(models.BankSession.created_at.desc())
        .first()
    )
    if not bank_session or not bank_session.token:
        raise HTTPException(status_code=400, detail="No bank account linked. Visit /auth/link first.")

    result = []
    for uid in bank_session.token.split(","):
        try:
            balances = enablebanking.get_balances(uid)
            result.append({"account_uid": uid, "balances": balances})
        except Exception as e:
            print(f"Error fetching balances for {uid}: {e}")
    return result


@app.post("/transactions/sync")
def sync_transactions(db: Session = Depends(get_db)):
    """
    Pull the latest transactions from all linked bank accounts and store
    any new ones in the local database.

    Uses `external_id` to skip duplicates — safe to call multiple times.
    """
    bank_session = (
        db.query(models.BankSession)
        .order_by(models.BankSession.created_at.desc())
        .first()
    )
    if not bank_session or not bank_session.token:
        raise HTTPException(status_code=400, detail="No bank account linked. Visit /auth/link first.")

    account_uids = bank_session.token.split(",")
    new_count = 0

    try:
        for uid in account_uids:
            txs = enablebanking.get_transactions(uid)

            for t in txs:
                # ── Parse amount ──────────────────────────────────────────────
                amount_info = t.get("transaction_amount") or {}
                amount      = float(amount_info.get("amount", 0))
                indicator   = t.get("credit_debit_indicator", "")  # "DBIT" or "CRDT"

                # Only treat as income if the bank explicitly marks it as a credit (CRDT).
                # SEB sometimes omits the indicator entirely for card purchases and
                # foreign transactions — those must default to expense, not income.
                # Pending/unprocessed transactions (no booking_date) also default to
                # expense because SEB's indicator is unreliable before settlement.
                is_pending = not t.get("booking_date")
                is_income = (not is_pending) and (indicator == "CRDT") and (amount > 0)
                tx_type   = "income" if is_income else "expense"

                # ── Derive a human-readable label for `category` ──────────────
                # Priority: creditor name (merchant) → remittance info → note
                creditor   = t.get("creditor") or {}
                remittance = t.get("remittance_information") or []
                category = (
                    creditor.get("name")
                    or (remittance[0] if remittance else None)
                    or t.get("note")
                    or "Other"
                )

                # ── Deduplication key ─────────────────────────────────────────
                # Use the bank's own reference if available, otherwise hash a
                # combination of fields that should uniquely identify the transaction.
                ext_id = (
                    t.get("entry_reference")
                    or t.get("reference_number")
                    or str(hash(f"{t.get('booking_date')}{amount}{t.get('note')}"))
                )

                if db.query(models.Transaction).filter(
                    models.Transaction.external_id == ext_id
                ).first():
                    continue  # already imported — skip

                # ── Parse date ────────────────────────────────────────────────
                booking_date_str = t.get("booking_date")
                booking_date = (
                    datetime.strptime(booking_date_str, "%Y-%m-%d").date()
                    if booking_date_str
                    else datetime.now().date()
                )

                print(f"SYNC: {tx_type.upper()} | {category} | {abs(amount)}")

                db.add(models.Transaction(
                    type=tx_type,
                    category=category[:50],       # column has no length limit but let's be tidy
                    amount=abs(amount),
                    date=booking_date,
                    note=t.get("note") or (remittance[0] if remittance else ""),
                    external_id=ext_id,
                ))
                new_count += 1

        db.commit()
        return {"status": "success", "new_transactions": new_count}

    except Exception as e:
        print(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Demo mode ─────────────────────────────────────────────────────────────────

DEMO_TRANSACTIONS = [
    # ── April 2025 ────────────────────────────────────────────────────────
    {"type": "income",  "category": "Lön",               "amount": 36500.00, "date": "2025-04-25", "note": "Månadslön april"},
    {"type": "expense", "category": "Hyra",              "amount": 9500.00,  "date": "2025-04-01", "note": "Hyra april"},
    {"type": "expense", "category": "SL",                "amount": 990.00,   "date": "2025-04-02", "note": "SL Månadskort"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1243.00,  "date": "2025-04-03", "note": "Mathandel"},
    {"type": "expense", "category": "Apotek Hjärtat",    "amount": 189.00,   "date": "2025-04-08", "note": "Apotek"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 876.00,   "date": "2025-04-10", "note": "Mathandel"},
    {"type": "expense", "category": "Restaurang Noi",    "amount": 340.00,   "date": "2025-04-12", "note": "Lunch"},
    {"type": "expense", "category": "Spotify",           "amount": 119.00,   "date": "2025-04-14", "note": "Spotify Premium"},
    {"type": "expense", "category": "Netflix",           "amount": 169.00,   "date": "2025-04-14", "note": "Netflix Premium"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1102.00,  "date": "2025-04-17", "note": "Mathandel"},
    {"type": "expense", "category": "Friskis & Svettis", "amount": 245.00,   "date": "2025-04-17", "note": "Gym månadsavgift"},
    {"type": "expense", "category": "Vattenfall",        "amount": 523.00,   "date": "2025-04-18", "note": "El"},
    {"type": "expense", "category": "H&M",               "amount": 799.00,   "date": "2025-04-19", "note": "Kläder"},
    {"type": "expense", "category": "McDonald's",        "amount": 132.00,   "date": "2025-04-21", "note": "Lunch"},
    {"type": "expense", "category": "Willys",            "amount": 445.00,   "date": "2025-04-22", "note": "Mathandel"},

    # ── March 2025 ────────────────────────────────────────────────────────
    {"type": "income",  "category": "Lön",               "amount": 36500.00, "date": "2025-03-25", "note": "Månadslön mars"},
    {"type": "expense", "category": "Hyra",              "amount": 9500.00,  "date": "2025-03-01", "note": "Hyra mars"},
    {"type": "expense", "category": "SL",                "amount": 990.00,   "date": "2025-03-02", "note": "SL Månadskort"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1087.00,  "date": "2025-03-04", "note": "Mathandel"},
    {"type": "expense", "category": "Apotek Hjärtat",    "amount": 134.00,   "date": "2025-03-06", "note": "Apotek"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 934.00,   "date": "2025-03-11", "note": "Mathandel"},
    {"type": "expense", "category": "Restaurang Noi",    "amount": 289.00,   "date": "2025-03-13", "note": "Lunch"},
    {"type": "expense", "category": "Spotify",           "amount": 119.00,   "date": "2025-03-14", "note": "Spotify Premium"},
    {"type": "expense", "category": "Netflix",           "amount": 169.00,   "date": "2025-03-14", "note": "Netflix Premium"},
    {"type": "expense", "category": "Friskis & Svettis", "amount": 245.00,   "date": "2025-03-17", "note": "Gym månadsavgift"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1211.00,  "date": "2025-03-18", "note": "Mathandel"},
    {"type": "expense", "category": "Vattenfall",        "amount": 612.00,   "date": "2025-03-19", "note": "El"},
    {"type": "expense", "category": "Zara",              "amount": 1199.00,  "date": "2025-03-22", "note": "Kläder"},
    {"type": "expense", "category": "Coop",              "amount": 378.00,   "date": "2025-03-25", "note": "Mathandel"},
    {"type": "expense", "category": "Swish",             "amount": 500.00,   "date": "2025-03-28", "note": "Swish till Erik"},
    {"type": "expense", "category": "Sushi Yama",        "amount": 430.00,   "date": "2025-03-29", "note": "Middag"},

    # ── February 2025 ─────────────────────────────────────────────────────
    {"type": "income",  "category": "Lön",               "amount": 36500.00, "date": "2025-02-25", "note": "Månadslön februari"},
    {"type": "expense", "category": "Hyra",              "amount": 9500.00,  "date": "2025-02-01", "note": "Hyra februari"},
    {"type": "expense", "category": "SL",                "amount": 990.00,   "date": "2025-02-03", "note": "SL Månadskort"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1156.00,  "date": "2025-02-03", "note": "Mathandel"},
    {"type": "expense", "category": "Apotek Hjärtat",    "amount": 245.00,   "date": "2025-02-07", "note": "Apotek"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 889.00,   "date": "2025-02-10", "note": "Mathandel"},
    {"type": "expense", "category": "Spotify",           "amount": 119.00,   "date": "2025-02-14", "note": "Spotify Premium"},
    {"type": "expense", "category": "Netflix",           "amount": 169.00,   "date": "2025-02-14", "note": "Netflix Premium"},
    {"type": "expense", "category": "Friskis & Svettis", "amount": 245.00,   "date": "2025-02-17", "note": "Gym månadsavgift"},
    {"type": "expense", "category": "Vattenfall",        "amount": 698.00,   "date": "2025-02-18", "note": "El"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1034.00,  "date": "2025-02-19", "note": "Mathandel"},
    {"type": "expense", "category": "Kebab Palace",      "amount": 145.00,   "date": "2025-02-20", "note": "Mat"},
    {"type": "expense", "category": "Telia",             "amount": 349.00,   "date": "2025-02-22", "note": "Mobilabonnemang"},
    {"type": "expense", "category": "Lidl",              "amount": 312.00,   "date": "2025-02-24", "note": "Mathandel"},

    # ── January 2025 ──────────────────────────────────────────────────────
    {"type": "income",  "category": "Lön",               "amount": 36500.00, "date": "2025-01-25", "note": "Månadslön januari"},
    {"type": "expense", "category": "Hyra",              "amount": 9500.00,  "date": "2025-01-01", "note": "Hyra januari"},
    {"type": "expense", "category": "SL",                "amount": 990.00,   "date": "2025-01-02", "note": "SL Månadskort"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1432.00,  "date": "2025-01-05", "note": "Mathandel"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 967.00,   "date": "2025-01-13", "note": "Mathandel"},
    {"type": "expense", "category": "Spotify",           "amount": 119.00,   "date": "2025-01-14", "note": "Spotify Premium"},
    {"type": "expense", "category": "Netflix",           "amount": 169.00,   "date": "2025-01-14", "note": "Netflix Premium"},
    {"type": "expense", "category": "H&M",               "amount": 599.00,   "date": "2025-01-15", "note": "Kläder"},
    {"type": "expense", "category": "Friskis & Svettis", "amount": 245.00,   "date": "2025-01-17", "note": "Gym månadsavgift"},
    {"type": "expense", "category": "Vattenfall",        "amount": 743.00,   "date": "2025-01-18", "note": "El"},
    {"type": "expense", "category": "ICA Maxi",          "amount": 1188.00,  "date": "2025-01-20", "note": "Mathandel"},
    {"type": "expense", "category": "Telia",             "amount": 349.00,   "date": "2025-01-22", "note": "Mobilabonnemang"},
    {"type": "expense", "category": "Circle K",          "amount": 756.00,   "date": "2025-01-22", "note": "Bensin"},
    {"type": "expense", "category": "Restaurang Noi",    "amount": 395.00,   "date": "2025-01-24", "note": "Middag"},
    {"type": "expense", "category": "Swish",             "amount": 300.00,   "date": "2025-01-28", "note": "Swish till Sara"},
]


@app.post("/demo/seed")
def seed_demo(db: Session = Depends(get_db)):
    """
    Wipe all transactions and load realistic mock data for demo purposes.
    Safe to call repeatedly — always resets to the same clean state.
    """
    db.query(models.Transaction).delete()

    for i, t in enumerate(DEMO_TRANSACTIONS):
        db.add(models.Transaction(
            type=t["type"],
            category=t["category"],
            amount=t["amount"],
            date=datetime.strptime(t["date"], "%Y-%m-%d").date(),
            note=t["note"],
            external_id=f"demo-{i}",
        ))

    db.commit()
    return {"seeded": len(DEMO_TRANSACTIONS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
