from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductTracker(Base):
    __tablename__ = "product_trackers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)

    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    network: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True)  # e.g., "rozetka", "allo"

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", backref="product_trackers")
    triggers = relationship("ProductTrackerTrigger", backref="tracker", cascade="all, delete-orphan")


class ProductTrackerTrigger(Base):
    __tablename__ = "product_tracker_triggers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(ForeignKey(
        "product_trackers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Valid types: "price_below", "price_rise", "discount", "back_in_stock",
    # "trade_in_available", "credit_available", "personal_price_available",
    # "gift_offer_available", "cashback_reach", "any_change"
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True)
