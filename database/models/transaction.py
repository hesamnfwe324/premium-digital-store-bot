import enum
from sqlalchemy import BigInteger, Integer, Float, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import Optional


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PURCHASE = "purchase"
    REFUND = "refund"
    REFERRAL_BONUS = "referral_bonus"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wallets.id"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance_before: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} type={self.transaction_type} amount={self.amount}>"
