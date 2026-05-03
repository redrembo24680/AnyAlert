from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductTracker(Base):
    __tablename__ = "product_trackers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)

    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    network: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True)  # e.g., "rozetka"
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Triggers
    # Valid types: "price_below", "price_drop", "back_in_stock"
    # - price_below/price_drop: trigger when price <= trigger_value
    # - back_in_stock: trigger when product becomes available
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_value: Mapped[float | None] = mapped_column(
        Float, nullable=True)  # target price for price-related triggers

    # Last parsed state
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float |
                                  None] = mapped_column(Float, nullable=True)
    last_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True)
    last_cashback_amount: Mapped[float |
                                 None] = mapped_column(Float, nullable=True)
    last_trade_in_available: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True)
    last_credit_available: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True)
    last_color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_memory_variant: Mapped[str | None] = mapped_column(
        String(100), nullable=True)
    last_delivery_available: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True)
    last_pickup_available: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True)
    last_personal_price_available: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True)
    last_gift_offer_available: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True)
    last_availability: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", backref="product_trackers")
