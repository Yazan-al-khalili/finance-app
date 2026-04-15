from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import models
import database
from pydantic import BaseModel
from datetime import date as date_type, datetime
import os
from dotenv import load_dotenv
from enablebanking_sdk.service import EnableBankingIntegration, EnableBankingService
from enablebanking_sdk.constants import PSUType
import uuid

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Configuration for Enable Banking
APP_ID = os.getenv("ENABLEBANKING_APP_ID")
CERT_PATH = os.path.join(os.path.dirname(__file__), "certificate.pem")
REDIRECT_URL = "http://localhost:8000/auth/callback"

# Create the database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
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

# Helper to get Enable Banking Service
def get_eb_service():
    if not APP_ID:
        # Check if .env actually exists
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        print(f"DEBUG: Checking for .env at {env_path}")
        if not os.path.exists(env_path):
            print("DEBUG: .env NOT FOUND")
        else:
            print("DEBUG: .env FOUND")
        raise HTTPException(status_code=500, detail="ENABLEBANKING_APP_ID not set in .env")
    
    try:
        with open(CERT_PATH, "r") as f:
            certificate = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Certificate not found at {CERT_PATH}")
    
    integration = EnableBankingIntegration(
        base_url="https://api.enablebanking.com",
        app_id=APP_ID,
        certificate=certificate
    )
    return EnableBankingService(integration)

# --- CORE ENDPOINTS ---

@app.get("/transactions", response_model=List[Transaction])
def get_transactions(db: Session = Depends(get_db)):
    try:
        return db.query(models.Transaction).order_by(models.Transaction.date.desc()).all()
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        # If DB is corrupted or missing column, recreate
        models.Base.metadata.create_all(bind=database.engine)
        return []

@app.post("/transactions", response_model=Transaction)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.delete("/transactions/{id}")
def delete_transaction(id: int, db: Session = Depends(get_db)):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_transaction)
    db.commit()
    return {"message": "Deleted"}

# --- ENABLE BANKING FLOW ---

@app.get("/auth/link")
def link_bank(country: str = "SE", bank_name: str = "Nordea"):
    service = get_eb_service()
    
    try:
        # 1. Search in both Personal and Business lists
        all_aspsps = []
        for p_type in [PSUType.PERSONAL, PSUType.BUSINESS]:
            try:
                all_aspsps.extend(service.get_aspsps(country=country, psu_type=p_type))
            except Exception as e:
                print(f"DEBUG: Error fetching {p_type} banks: {e}")
                continue
        
        # 2. Try to find the requested bank (e.g. Nordea)
        target_bank = next((a for a in all_aspsps if bank_name.upper() in a.name.upper()), None)
        
        # 3. If not found, look for "MOCK"
        if not target_bank:
            print(f"DEBUG: {bank_name} not found in {country}. Falling back to Mock ASPSP.")
            target_bank = next((a for a in all_aspsps if "MOCK" in a.name.upper()), None)
        
        if not target_bank:
            available = [a.name for a in all_aspsps]
            print(f"DEBUG: Available banks in {country}: {available}")
            raise HTTPException(status_code=404, detail=f"No suitable bank found. Available: {available[:5]}...")
        
        print(f"DEBUG: Starting session for {target_bank.name} in {target_bank.country}")

        # 4. Start user session
        state = str(uuid.uuid4())
        try:
            session_response = service.start_user_session(
                aspsp=target_bank,
                state=state,
                redirect_url=REDIRECT_URL,
                language="en",
                psu_type=PSUType.PERSONAL
            )
            return {"url": session_response.url}
        except Exception as api_error:
            # Try to extract the detailed error message from the response
            if hasattr(api_error, 'response') and api_error.response is not None:
                print(f"DEBUG: Enable Banking API Error Detail: {api_error.response.text}")
            
            print(f"DEBUG: Enable Banking API Error: {api_error}")
            raise HTTPException(status_code=400, detail=f"Bank API Error: {str(api_error)}")
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Error in link_bank: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/callback")
def auth_callback(code: str, state: str, db: Session = Depends(get_db)):
    service = get_eb_service()
    
    # 1. Authorize session and get accounts
    response = service.authorize_user_session(code)
    
    # 2. Store account UIDs to fetch transactions later
    # We store them in our BankSession table (token field for simplicity)
    account_uids = ",".join([acc.uid for acc in response.accounts])
    
    bank_session = models.BankSession(
        aspsp_id=response.aspsp.name,
        session_id=response.session_id,
        token=account_uids # Storing UIDs here
    )
    db.add(bank_session)
    db.commit()
    
    return RedirectResponse(url="http://localhost:5173/?sync=success")

@app.post("/transactions/sync")
def sync_transactions(db: Session = Depends(get_db)):
    bank_session = db.query(models.BankSession).order_by(models.BankSession.created_at.desc()).first()
    if not bank_session or not bank_session.token:
        raise HTTPException(status_code=400, detail="No bank account linked")
    
    service = get_eb_service()
    account_uids = bank_session.token.split(",")
    new_count = 0
    
    try:
        for uid in account_uids:
            txs = service.get_account_transactions(uid)
            for t in txs:
                # 1. Generate a robust external_id
                ext_id = t.entry_reference or t.reference_number or str(hash(f"{t.booking_date}{t.transaction_amount.amount}{t.note}"))
                
                existing = db.query(models.Transaction).filter(models.Transaction.external_id == ext_id).first()
                if not existing:
                    amount = t.transaction_amount.amount
                    indicator = t.credit_debit_indicator # DBIT or CRDT
                    
                    # 2. Logic: If indicator is DBIT OR amount is negative, it's an expense
                    is_expense = (indicator == "DBIT") or (amount < 0)
                    tx_type = "expense" if is_expense else "income"
                    
                    # 3. Smarter Category/Name extraction
                    # Try Creditor Name (Merchant), then Note, then fallback
                    category = "Other"
                    if t.creditor and t.creditor.name:
                        category = t.creditor.name
                    elif t.remittance_information and len(t.remittance_information) > 0:
                        category = t.remittance_information[0]
                    elif t.note:
                        category = t.note
                    
                    print(f"DEBUG SYNC: {tx_type.upper()} | {category} | {abs(amount)}")

                    new_tx = models.Transaction(
                        type=tx_type,
                        category=category[:50], # Limit length
                        amount=abs(amount),
                        date=datetime.strptime(t.booking_date, "%Y-%m-%d").date() if t.booking_date else datetime.now().date(),
                        note=t.note or (t.remittance_information[0] if t.remittance_information else ""),
                        external_id=ext_id
                    )
                    db.add(new_tx)
                    new_count += 1
        
        db.commit()
        return {"status": "success", "new_transactions": new_count}
        
    except Exception as e:
        print(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
