from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import Optional


class VisaCard(Base):
    __tablename__ = "visa_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    card_number: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    cvv: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    expiry_month: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    expiry_year: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    cardholder_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    balance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    card_type: Mapped[str] = mapped_column(String(50), default="virtual", nullable=False)
    extra_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("orders.id"), nullable=True)
    added_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="visa_cards")

    def __repr__(self) -> str:
        return f"<VisaCard id={self.id} type={self.card_type} sold={self.is_sold}>"
