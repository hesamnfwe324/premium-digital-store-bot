import enum
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import Optional, List


class ProductCategory(str, enum.Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    GIFT_CARD = "gift_card"
    PREMIUM_SERVICE = "premium_service"


class ProductType(str, enum.Enum):
    VIRTUAL_VISA = "virtual_visa"
    PHYSICAL_VISA = "physical_visa"
    RELOADABLE_VISA = "reloadable_visa"
    CUSTOM_BALANCE_VISA = "custom_balance_visa"
    VIRTUAL_MASTERCARD = "virtual_mastercard"
    PHYSICAL_MASTERCARD = "physical_mastercard"
    INTERNATIONAL_MASTERCARD = "international_mastercard"
    CUSTOM_MASTERCARD = "custom_mastercard"
    GIFT_CARD = "gift_card"
    PREMIUM_SERVICE = "premium_service"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_es: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_fr: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_de: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_ru: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_zh: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_ar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_fa: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[ProductCategory] = mapped_column(Enum(ProductCategory), nullable=False)
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    price_usdt: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_time: Mapped[str] = mapped_column(String(100), default="Instant", nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gift_card_brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="product")
    gift_cards: Mapped[List["GiftCard"]] = relationship("GiftCard", back_populates="product")
    visa_cards: Mapped[List["VisaCard"]] = relationship("VisaCard", back_populates="product")
    master_cards: Mapped[List["MasterCard"]] = relationship("MasterCard", back_populates="product")

    def get_name(self, lang: str) -> str:
        return getattr(self, f"name_{lang}", None) or self.name_en or self.name

    def get_description(self, lang: str) -> str:
        return getattr(self, f"description_{lang}", None) or self.description_en or self.description or ""

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name}>"
