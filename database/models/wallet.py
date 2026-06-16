from sqlalchemy import BigInteger, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import List


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), unique=True, nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_deposited: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_withdrawn: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_earned_referral: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="wallet")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="wallet")

    def __repr__(self) -> str:
        return f"<Wallet user_id={self.user_telegram_id} balance={self.balance}>"
