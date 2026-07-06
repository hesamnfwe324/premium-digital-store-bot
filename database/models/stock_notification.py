from sqlalchemy import Integer, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime


class StockNotification(Base):
    __tablename__ = "stock_notifications"

    __table_args__ = (
        UniqueConstraint("product_id", "user_telegram_id", "notified", name="uq_stock_notif_pending"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="stock_notifications")

    def __repr__(self) -> str:
        return f"<StockNotification product_id={self.product_id} user={self.user_telegram_id} notified={self.notified}>"
