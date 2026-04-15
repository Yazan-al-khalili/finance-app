from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from database import Base
import datetime

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # income or expense
    category = Column(String)
    amount = Column(Float)
    date = Column(Date)
    note = Column(String, nullable=True)
    external_id = Column(String, unique=True, nullable=True) # To prevent duplicates from bank

class BankSession(Base):
    __tablename__ = "bank_sessions"

    id = Column(Integer, primary_key=True, index=True)
    aspsp_id = Column(String)
    session_id = Column(String)
    token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
