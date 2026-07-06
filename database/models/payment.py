import enum
from sqlalchemy import BigInteger, Integer, Float, String, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import Optional, List


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CryptoCurrency(str, enum.Enum):
    USDT_TRC20 = "USDT_TRC20"
    USDT_BEP20 = "USDT_BEP20"
    BTC = "BTC"
    ETH = "ETH"
    BNB = "BNB"
    TON = "TON"


CRYPTO_NETWORK_NAMES = {
    CryptoCurrency.USDT_TRC20: "USDT (TRC20 / TRON)",
    CryptoCurrency.USDT_BEP20: "USDT (BEP20 / BSC)",
    CryptoCurrency.BTC: "Bitcoin (BTC)",
    CryptoCurrency.ETH: "Ethereum (ETH)",
    CryptoCurrency.BNB: "BNB (BEP20)",
    CryptoCurrency.TON: "TON (The Open Network)",
}

CRYPTO_EMOJIS = {
    CryptoCurrency.USDT_TRC20: "🟢",
    CryptoCurrency.USDT_BEP20: "🔶",
    CryptoCurrency.BTC: "🟡",
    CryptoCurrency.ETH: "💠",
    CryptoCurrency.BNB: "🟠",
    CryptoCurrency.TON: "💎",
}


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount_usdt: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[CryptoCurrency] = mapped_column(Enum(CryptoCurrency), nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(500), nullable=False)
    txid: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transaction_link: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed_by_admin: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_wallet_deposit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")

    order: Mapped[Optional["Order"]] = relationship("Order", back_populates="payment", foreign_keys="Order.payment_id")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} ref={self.payment_reference} status={self.status}>"
