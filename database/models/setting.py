from sqlalchemy import Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import Optional


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Setting key={self.key} value={self.value}>"
