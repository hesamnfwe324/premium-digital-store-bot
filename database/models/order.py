import enum
from sqlalchemy import BigInteger, Integer, Float, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import Optional


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAYMENT_RECEIVED = "payment_received"
    VALIDATING = "validating"
    PREPARING = "preparing"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


ORDER_STATUS_EMOJI = {
    OrderStatus.PENDING: "⏳",
    OrderStatus.PAYMENT_RECEIVED: "💰",
    OrderStatus.VALIDATING: "🔍",
    OrderStatus.PREPARING: "📦",
    OrderStatus.DELIVERING: "🚀",
    OrderStatus.DELIVERED: "✅",
    OrderStatus.CANCELLED: "❌",
    OrderStatus.REJECTED: "❌",
}


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("payments.id"), nullable=True)
    discount_code_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("discount_codes.id"), nullable=True)
    delivered_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="orders", foreign_keys=[user_telegram_id])
    product: Mapped["Product"] = relationship("Product", back_populates="orders")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="order", foreign_keys=[payment_id])
    discount_code: Mapped[Optional["DiscountCode"]] = relationship("DiscountCode", back_populates="orders")

    @property
    def status_emoji(self) -> str:
        return ORDER_STATUS_EMOJI.get(self.status, "❓")

    def __repr__(self) -> str:
        return f"<Order id={self.id} order_number={self.order_number} status={self.status}>"
