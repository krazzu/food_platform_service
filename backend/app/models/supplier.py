from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index,
    Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    parent: Mapped[Optional["Category"]] = relationship("Category", remote_side=[id], back_populates="children")
    children: Mapped[list["Category"]] = relationship("Category", back_populates="parent")
    suppliers: Mapped[list["Supplier"]] = relationship("Supplier", back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Contacts
    website: Mapped[Optional[str]] = mapped_column(String(512))
    email: Mapped[Optional[str]] = mapped_column(String(256))
    phone: Mapped[Optional[str]] = mapped_column(String(64))

    # Location
    city: Mapped[Optional[str]] = mapped_column(String(128))
    region: Mapped[Optional[str]] = mapped_column(String(128))
    delivery_regions: Mapped[Optional[list]] = mapped_column(JSON)  # ["Москва", "МО", ...]

    # Category
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"))
    category: Mapped[Optional[Category]] = relationship("Category", back_populates="suppliers")

    # Order & pricing
    min_order_amount: Mapped[Optional[float]] = mapped_column(Float)
    min_order_unit: Mapped[Optional[str]] = mapped_column(String(32))  # "руб", "кг", "упак"
    price_range_description: Mapped[Optional[str]] = mapped_column(String(256))

    # Compliance
    has_certificates: Mapped[bool] = mapped_column(Boolean, default=False)
    certificate_types: Mapped[Optional[list]] = mapped_column(JSON)  # ["ГОСТ", "ISO", ...]

    # Delivery
    delivery_conditions: Mapped[Optional[str]] = mapped_column(Text)

    # Source
    source_url: Mapped[Optional[str]] = mapped_column(String(1024))
    source_platform: Mapped[Optional[str]] = mapped_column(String(64))  # "seed", "agroserver", ...

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # B2B extra fields
    inn: Mapped[Optional[str]] = mapped_column(String(12))               # ИНН
    legal_name: Mapped[Optional[str]] = mapped_column(String(512))       # Официальное название юрлица
    verified: Mapped[bool] = mapped_column(Boolean, default=False)       # Вручную проверен
    rating: Mapped[Optional[float]] = mapped_column(Float)               # Рейтинг 1.0–5.0
    payment_terms: Mapped[Optional[str]] = mapped_column(String(256))    # Условия оплаты
    works_with_nds: Mapped[Optional[bool]] = mapped_column(Boolean)      # Работает с НДС

    # Freshness tracking
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Indexes for common filter patterns
Index("ix_suppliers_region",          Supplier.region)
Index("ix_suppliers_category_id",     Supplier.category_id)
Index("ix_suppliers_is_stale",        Supplier.is_stale)
Index("ix_suppliers_city",            Supplier.city)
Index("ix_suppliers_min_order",       Supplier.min_order_amount)
Index("ix_suppliers_has_certs",       Supplier.has_certificates)
Index("ix_suppliers_verified",        Supplier.verified)
Index("ix_suppliers_inn",             Supplier.inn)
Index("ix_suppliers_region_category", Supplier.region, Supplier.category_id)
