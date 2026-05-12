from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RozetkaTrackerData(Base):
    """Rozetka-specific product tracking data"""
    __tablename__ = "rozetka_tracker_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_cashback_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_availability: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_trade_in_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_credit_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_gift_offer_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_personal_price_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class OlxTrackerData(Base):
    """OLX-specific product tracking data"""
    __tablename__ = "olx_tracker_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_availability: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PromTrackerData(Base):
    """PROM-specific product tracking data"""
    __tablename__ = "prom_tracker_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_availability: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AlloTrackerData(Base):
    """ALLO-specific product tracking data"""
    __tablename__ = "allo_tracker_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_cashback_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_personal_price_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_gift_offer_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_availability: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_trade_in_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_credit_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_delivery_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_pickup_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_memory_variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ComfyTrackerData(Base):
    """COMFY-specific product tracking data"""
    __tablename__ = "comfy_tracker_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_cashback_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_personal_price_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_gift_offer_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_availability: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_trade_in_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_credit_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_delivery_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_pickup_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_memory_variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class FoxtrotTrackerData(Base):
    """FOXTROT-specific product tracking data"""
    __tablename__ = "foxtrot_tracker_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_cashback_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_personal_price_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_gift_offer_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_availability: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_trade_in_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_credit_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_delivery_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_pickup_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_memory_variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ComfyOffersData(Base):
    """COMFY offers-specific tracking data"""
    __tablename__ = "comfy_offers_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_cashback_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_personal_price_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_gift_offer_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_memory_variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class FoxtrotOffersData(Base):
    """FOXTROT offers-specific tracking data"""
    __tablename__ = "foxtrot_offers_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracker_id: Mapped[int] = mapped_column(
        ForeignKey("product_trackers.id", ondelete="CASCADE"), nullable=False
    )

    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_cashback_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_personal_price_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_gift_offer_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_memory_variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
