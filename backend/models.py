from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # income or expense
    category = Column(String)
    amount = Column(Float)
    date = Column(Date)
    note = Column(String, nullable=True)
