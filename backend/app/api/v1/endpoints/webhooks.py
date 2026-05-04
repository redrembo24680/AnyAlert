"""
Webhook endpoints for parsers to submit platform-specific tracker data.
Endpoints: /api/v1/webhooks/{tracker_id}/rozetka, /allo, /comfy, etc.
"""
from datetime import datetime
import asyncio
import logging
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.api.deps import get_db
from app.models.tracker import ProductTracker
from app.models.tracker import ProductTrackerTrigger
from app.models.user import User
from app.models.platform_data import (
    RozetkaTrackerData,
    OlxTrackerData,
    PromTrackerData,
    AlloTrackerData,
    ComfyTrackerData,
    FoxtrotTrackerData,
    ComfyOffersData,
    FoxtrotOffersData,
)

router = APIRouter()

logger = logging.getLogger(__name__)

from app.dependencies import get_email_service
from app.services.email_service import EmailService


def _parse_iso_datetime(dt_string: str | None) -> datetime | None:
    """Parse ISO 8601 datetime string to Python datetime object."""
    if dt_string is None:
        return None
    if isinstance(dt_string, datetime):
        return dt_string
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


async def _evaluate_triggers_and_notify(
    db: AsyncSession,
    email_service: EmailService,
    tracker_id: int,
    old_price: float | None,
    new_price: float | None,
) -> None:
    """Evaluate active triggers for tracker and schedule email notifications."""
    def _fmt(value: float | None) -> str:
        return "N/A" if value is None else str(value)

    try:
        triggers_stmt = select(ProductTrackerTrigger).where(
            ProductTrackerTrigger.tracker_id == tracker_id,
            ProductTrackerTrigger.is_active == True,
        )
        trig_res = await db.execute(triggers_stmt)
        triggers = trig_res.scalars().all()

        if not triggers:
            return

        tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
        tr_res = await db.execute(tracker_stmt)
        tracker = tr_res.scalars().first()
        if not tracker:
            return

        user_stmt = select(User).where(User.id == tracker.user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalars().first()
        if not user or not user.email:
            return

        fired_trigger_ids: list[int] = []

        for trig in triggers:
            if (
                trig.trigger_type == "price_below"
                and new_price is not None
                and trig.trigger_value is not None
                and new_price < trig.trigger_value
            ):
                logger.info(
                    "Scheduling trigger notification for tracker %s user %s type %s",
                    tracker_id,
                    user.email,
                    trig.trigger_type,
                )
                asyncio.create_task(
                    email_service.send_trigger_notification(
                        user.email,
                        tracker.url,
                        _fmt(trig.trigger_value),
                        _fmt(new_price),
                        trig.trigger_type,
                    )
                )
                fired_trigger_ids.append(trig.id)
            elif trig.trigger_type == "any_change":
                changed = False
                if old_price is None and new_price is not None:
                    changed = True
                elif old_price is not None and new_price is not None and old_price != new_price:
                    changed = True

                if changed:
                    logger.info(
                        "Scheduling any_change notification for tracker %s user %s",
                        tracker_id,
                        user.email,
                    )
                    asyncio.create_task(
                        email_service.send_trigger_notification(
                            user.email,
                            tracker.url,
                            _fmt(old_price),
                            _fmt(new_price),
                            trig.trigger_type,
                        )
                    )
                    fired_trigger_ids.append(trig.id)

        if fired_trigger_ids:
            for trig in triggers:
                if trig.id in fired_trigger_ids:
                    trig.is_active = False

            active_left = [tr for tr in triggers if tr.is_active]
            if not active_left:
                tracker.is_active = False

            await db.commit()

            logger.info(
                "Deactivated %s fired triggers for tracker %s; tracker_active=%s",
                len(fired_trigger_ids),
                tracker_id,
                tracker.is_active,
            )
    except Exception:
        logger.exception("Failed to evaluate triggers for tracker %s", tracker_id)


class RozetkaWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_status: str | None = None
    last_availability: bool | None = None
    last_rating: float | None = None
    last_views: int | None = None
    last_reviews_count: int | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/rozetka")
async def webhook_rozetka(
    tracker_id: int = Path(...),
    data: RozetkaWebhookData = Body(...),
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Rozetka parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    existing_stmt = select(RozetkaTrackerData).where(
        RozetkaTrackerData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    # Capture old values for trigger evaluation
    old_price = existing.last_price if existing else None
    
    if existing:
        existing.last_price = data.last_price
        existing.last_old_price = data.last_old_price
        existing.last_discount_percent = data.last_discount_percent
        existing.last_status = data.last_status
        existing.last_availability = data.last_availability
        existing.last_rating = data.last_rating
        existing.last_views = data.last_views
        existing.last_reviews_count = data.last_reviews_count
        existing.last_checked_at = _parse_iso_datetime(data.last_checked_at)
    else:
        record = RozetkaTrackerData(
            tracker_id=tracker_id,
            last_price=data.last_price,
            last_old_price=data.last_old_price,
            last_discount_percent=data.last_discount_percent,
            last_status=data.last_status,
            last_availability=data.last_availability,
            last_rating=data.last_rating,
            last_views=data.last_views,
            last_reviews_count=data.last_reviews_count,
            last_checked_at=_parse_iso_datetime(data.last_checked_at),
        )
        db.add(record)
    
    await db.commit()

    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
    )
    return {"status": "ok"}


class OlxWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_status: str | None = None
    last_availability: bool | None = None
    last_rating: float | None = None
    last_reviews_count: int | None = None
    last_views: int | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/olx")
async def webhook_olx(
    tracker_id: int = Path(...),
    data: OlxWebhookData = Body(...),
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """OLX parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    existing_stmt = select(OlxTrackerData).where(
        OlxTrackerData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    old_price = existing.last_price if existing else None
    
    if existing:
        existing.last_price = data.last_price
        existing.last_old_price = data.last_old_price
        existing.last_discount_percent = data.last_discount_percent
        existing.last_status = data.last_status
        existing.last_availability = data.last_availability
        existing.last_rating = data.last_rating
        existing.last_reviews_count = data.last_reviews_count
        existing.last_views = data.last_views
        existing.last_checked_at = _parse_iso_datetime(data.last_checked_at)
    else:
        record = OlxTrackerData(
            tracker_id=tracker_id,
            last_price=data.last_price,
            last_old_price=data.last_old_price,
            last_discount_percent=data.last_discount_percent,
            last_status=data.last_status,
            last_availability=data.last_availability,
            last_rating=data.last_rating,
            last_reviews_count=data.last_reviews_count,
            last_views=data.last_views,
            last_checked_at=_parse_iso_datetime(data.last_checked_at),
        )
        db.add(record)
    
    await db.commit()
    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
    )
    return {"status": "ok"}


class PromWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_status: str | None = None
    last_availability: bool | None = None
    last_rating: float | None = None
    last_views: int | None = None
    last_reviews_count: int | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/prom")
async def webhook_prom(
    tracker_id: int = Path(...),
    data: PromWebhookData = Body(...),
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Prom parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    existing_stmt = select(PromTrackerData).where(
        PromTrackerData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    old_price = existing.last_price if existing else None
    
    if existing:
        existing.last_price = data.last_price
        existing.last_old_price = data.last_old_price
        existing.last_discount_percent = data.last_discount_percent
        existing.last_status = data.last_status
        existing.last_availability = data.last_availability
        existing.last_rating = data.last_rating
        existing.last_views = data.last_views
        existing.last_reviews_count = data.last_reviews_count
        existing.last_checked_at = _parse_iso_datetime(data.last_checked_at)
    else:
        record = PromTrackerData(
            tracker_id=tracker_id,
            last_price=data.last_price,
            last_old_price=data.last_old_price,
            last_discount_percent=data.last_discount_percent,
            last_status=data.last_status,
            last_availability=data.last_availability,
            last_rating=data.last_rating,
            last_views=data.last_views,
            last_reviews_count=data.last_reviews_count,
            last_checked_at=_parse_iso_datetime(data.last_checked_at),
        )
        db.add(record)
    
    await db.commit()
    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
    )
    return {"status": "ok"}


class AlloWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_status: str | None = None
    last_availability: bool | None = None
    last_rating: float | None = None
    last_reviews_count: int | None = None
    last_cashback_amount: float | None = None
    last_trade_in_available: bool | None = None
    last_credit_available: bool | None = None
    last_color: str | None = None
    last_memory_variant: str | None = None
    last_delivery_available: bool | None = None
    last_pickup_available: bool | None = None
    last_personal_price_available: bool | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/allo")
async def webhook_allo(
    tracker_id: int = Path(...),
    data: AlloWebhookData = Body(...),
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Allo parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    existing_stmt = select(AlloTrackerData).where(
        AlloTrackerData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    old_price = existing.last_price if existing else None
    
    if existing:
        for field, value in data.model_dump().items():
            if field == "last_checked_at":
                setattr(existing, field, _parse_iso_datetime(value))
            else:
                setattr(existing, field, value)
    else:
        record = AlloTrackerData(
            tracker_id=tracker_id,
            last_price=data.last_price,
            last_old_price=data.last_old_price,
            last_discount_percent=data.last_discount_percent,
            last_status=data.last_status,
            last_availability=data.last_availability,
            last_rating=data.last_rating,
            last_reviews_count=data.last_reviews_count,
            last_cashback_amount=data.last_cashback_amount,
            last_trade_in_available=data.last_trade_in_available,
            last_credit_available=data.last_credit_available,
            last_color=data.last_color,
            last_memory_variant=data.last_memory_variant,
            last_delivery_available=data.last_delivery_available,
            last_pickup_available=data.last_pickup_available,
            last_personal_price_available=data.last_personal_price_available,
            last_checked_at=_parse_iso_datetime(data.last_checked_at),
        )
        db.add(record)
    
    await db.commit()
    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
    )
    return {"status": "ok"}


class ComfyWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_status: str | None = None
    last_availability: bool | None = None
    last_rating: float | None = None
    last_reviews_count: int | None = None
    last_cashback_amount: float | None = None
    last_personal_price_available: bool | None = None
    last_color: str | None = None
    last_memory_variant: str | None = None
    last_delivery_available: bool | None = None
    last_pickup_available: bool | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/comfy")
async def webhook_comfy(
    tracker_id: int = Path(...),
    data: ComfyWebhookData = Body(...),
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Comfy parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    existing_stmt = select(ComfyTrackerData).where(
        ComfyTrackerData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    old_price = existing.last_price if existing else None
    
    if existing:
        for field, value in data.model_dump().items():
            if field == "last_checked_at":
                setattr(existing, field, _parse_iso_datetime(value))
            else:
                setattr(existing, field, value)
    else:
        record = ComfyTrackerData(
            tracker_id=tracker_id,
            last_price=data.last_price,
            last_old_price=data.last_old_price,
            last_discount_percent=data.last_discount_percent,
            last_status=data.last_status,
            last_availability=data.last_availability,
            last_rating=data.last_rating,
            last_reviews_count=data.last_reviews_count,
            last_cashback_amount=data.last_cashback_amount,
            last_personal_price_available=data.last_personal_price_available,
            last_color=data.last_color,
            last_memory_variant=data.last_memory_variant,
            last_delivery_available=data.last_delivery_available,
            last_pickup_available=data.last_pickup_available,
            last_checked_at=_parse_iso_datetime(data.last_checked_at),
        )
        db.add(record)
    
    await db.commit()
    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
    )
    return {"status": "ok"}


class ComfyOffersWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_cashback_amount: float | None = None
    last_reviews_count: int | None = None
    last_views: int | None = None
    last_personal_price_available: bool | None = None
    last_gift_offer_available: bool | None = None
    last_color: str | None = None
    last_memory_variant: str | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/comfy-offers")
async def webhook_comfy_offers(
    tracker_id: int = Path(...),
    data: ComfyOffersWebhookData = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Comfy offers parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    record = ComfyOffersData(
        tracker_id=tracker_id,
        last_price=data.last_price,
        last_old_price=data.last_old_price,
        last_discount_percent=data.last_discount_percent,
        last_cashback_amount=data.last_cashback_amount,
        last_reviews_count=data.last_reviews_count,
        last_views=data.last_views,
        last_personal_price_available=data.last_personal_price_available,
        last_gift_offer_available=data.last_gift_offer_available,
        last_color=data.last_color,
        last_memory_variant=data.last_memory_variant,
        last_checked_at=_parse_iso_datetime(data.last_checked_at),
    )
    db.add(record)
    await db.commit()
    return {"status": "ok"}


class FoxtrotWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_status: str | None = None
    last_availability: bool | None = None
    last_rating: float | None = None
    last_reviews_count: int | None = None
    last_cashback_amount: float | None = None
    last_trade_in_available: bool | None = None
    last_credit_available: bool | None = None
    last_color: str | None = None
    last_memory_variant: str | None = None
    last_delivery_available: bool | None = None
    last_pickup_available: bool | None = None
    last_gift_offer_available: bool | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/foxtrot")
async def webhook_foxtrot(
    tracker_id: int = Path(...),
    data: FoxtrotWebhookData = Body(...),
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Foxtrot parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    existing_stmt = select(FoxtrotTrackerData).where(
        FoxtrotTrackerData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    old_price = existing.last_price if existing else None
    
    if existing:
        for field, value in data.model_dump().items():
            if field == "last_checked_at":
                setattr(existing, field, _parse_iso_datetime(value))
            else:
                setattr(existing, field, value)
    else:
        record = FoxtrotTrackerData(
            tracker_id=tracker_id,
            last_price=data.last_price,
            last_old_price=data.last_old_price,
            last_discount_percent=data.last_discount_percent,
            last_status=data.last_status,
            last_availability=data.last_availability,
            last_rating=data.last_rating,
            last_reviews_count=data.last_reviews_count,
            last_cashback_amount=data.last_cashback_amount,
            last_trade_in_available=data.last_trade_in_available,
            last_credit_available=data.last_credit_available,
            last_color=data.last_color,
            last_memory_variant=data.last_memory_variant,
            last_delivery_available=data.last_delivery_available,
            last_pickup_available=data.last_pickup_available,
            last_gift_offer_available=data.last_gift_offer_available,
            last_checked_at=_parse_iso_datetime(data.last_checked_at),
        )
        db.add(record)
    
    await db.commit()
    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
    )
    return {"status": "ok"}


class FoxtrotOffersWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_cashback_amount: float | None = None
    last_reviews_count: int | None = None
    last_views: int | None = None
    last_personal_price_available: bool | None = None
    last_gift_offer_available: bool | None = None
    last_color: str | None = None
    last_memory_variant: str | None = None
    last_checked_at: str | None = None


@router.post("/{tracker_id}/foxtrot-offers")
async def webhook_foxtrot_offers(
    tracker_id: int = Path(...),
    data: FoxtrotOffersWebhookData = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Foxtrot offers parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    record = FoxtrotOffersData(
        tracker_id=tracker_id,
        last_price=data.last_price,
        last_old_price=data.last_old_price,
        last_discount_percent=data.last_discount_percent,
        last_cashback_amount=data.last_cashback_amount,
        last_reviews_count=data.last_reviews_count,
        last_views=data.last_views,
        last_personal_price_available=data.last_personal_price_available,
        last_gift_offer_available=data.last_gift_offer_available,
        last_color=data.last_color,
        last_memory_variant=data.last_memory_variant,
        last_checked_at=_parse_iso_datetime(data.last_checked_at),
    )
    db.add(record)
    await db.commit()
    return {"status": "ok"}
