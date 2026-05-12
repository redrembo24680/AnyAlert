"""
Webhook endpoints for parsers to submit platform-specific tracker data.
Endpoints: /api/v1/webhooks/{tracker_id}/rozetka, /allo, /comfy, etc.
"""
from datetime import datetime
import asyncio
import logging
from types import SimpleNamespace
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
from app.services import telegram_service


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


def _snapshot_for_trigger_eval(existing: object | None) -> object | None:
    if existing is None:
        return None

    fields = (
        "last_availability",
        "last_discount_percent",
        "last_cashback_amount",
        "last_trade_in_available",
        "last_credit_available",
        "last_gift_offer_available",
        "last_personal_price_available",
    )
    return SimpleNamespace(**{field: getattr(existing, field, None) for field in fields})


def _schedule_notification_email(
    email_service: EmailService,
    recipient_email: str,
    url: str,
    old_value: str,
    new_value: str,
    trigger_type: str,
    tracker_id: int,
) -> None:
    task = asyncio.create_task(
        email_service.send_trigger_notification(
            recipient_email,
            url,
            old_value,
            new_value,
            trigger_type,
        )
    )

    def _on_done(done_task: asyncio.Task) -> None:
        exc = done_task.exception()
        if exc:
            logger.exception(
                "Email send failed for tracker %s trigger %s recipient %s",
                tracker_id,
                trigger_type,
                recipient_email,
                exc_info=exc,
            )
        else:
            logger.info(
                "Email sent for tracker %s trigger %s recipient %s",
                tracker_id,
                trigger_type,
                recipient_email,
            )

    task.add_done_callback(_on_done)


_TRIGGER_TYPE_LABELS: dict[str, str] = {
    "price_below": "Ціна нижче порогу",
    "price_rise": "Ціна перевищила поріг",
    "any_change": "Зміна ціни",
    "back_in_stock": "Товар знову в наявності",
    "discount": "Знижка",
    "cashback_reach": "Кешбек досяг порогу",
    "trade_in_available": "Trade-in доступний",
    "credit_available": "Кредит доступний",
    "gift_offer_available": "Подарунок доступний",
    "personal_price_available": "Персональна ціна доступна",
}


def _schedule_notification_telegram(
    telegram_id: int,
    url: str,
    old_value: str,
    new_value: str,
    trigger_type: str,
    tracker_id: int,
) -> None:
    label = _TRIGGER_TYPE_LABELS.get(trigger_type, trigger_type)
    text = (
        f"🔔 <b>AnyAlert: {label}</b>\n\n"
        f"📦 <a href=\"{url}\">Переглянути товар</a>\n"
        f"📉 Попереднє: <b>{old_value}</b>\n"
        f"📈 Нове: <b>{new_value}</b>"
    )
    task = asyncio.create_task(telegram_service.send_message(telegram_id, text))

    def _on_tg_done(done_task: asyncio.Task) -> None:
        exc = done_task.exception()
        if exc:
            logger.exception(
                "Telegram send failed for tracker %s trigger %s telegram_id %s",
                tracker_id, trigger_type, telegram_id, exc_info=exc,
            )

    task.add_done_callback(_on_tg_done)


def _schedule_all_notifications(
    email_service: EmailService,
    user_email: str,
    telegram_id: int | None,
    url: str,
    old_value: str,
    new_value: str,
    trigger_type: str,
    tracker_id: int,
) -> None:
    _schedule_notification_email(
        email_service=email_service,
        recipient_email=user_email,
        url=url,
        old_value=old_value,
        new_value=new_value,
        trigger_type=trigger_type,
        tracker_id=tracker_id,
    )
    if telegram_id:
        _schedule_notification_telegram(
            telegram_id=telegram_id,
            url=url,
            old_value=old_value,
            new_value=new_value,
            trigger_type=trigger_type,
            tracker_id=tracker_id,
        )


async def _evaluate_triggers_and_notify(
    db: AsyncSession,
    email_service: EmailService,
    tracker_id: int,
    old_price: float | None,
    new_price: float | None,
    existing: object | None = None,
    new_data: dict | None = None,
) -> None:
    """Evaluate active triggers for tracker and schedule email notifications.

    Accepts optional `existing` (previous tracker data record) and `new_data`
    dict produced by the webhook so various non-price trigger types can be
    evaluated (back_in_stock, discount, cashback_reach, trade_in_available, etc.).
    """
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
            # price_below
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
                _schedule_all_notifications(
                    email_service=email_service,
                    user_email=user.email,
                    telegram_id=user.telegram_id,
                    url=tracker.url,
                    old_value=_fmt(trig.trigger_value),
                    new_value=_fmt(new_price),
                    trigger_type=trig.trigger_type,
                    tracker_id=tracker_id,
                )
                fired_trigger_ids.append(trig.id)
            # price_rise
            elif (
                trig.trigger_type == "price_rise"
                and new_price is not None
                and trig.trigger_value is not None
                and new_price > trig.trigger_value
            ):
                logger.info(
                    "Scheduling trigger notification for tracker %s user %s type %s",
                    tracker_id,
                    user.email,
                    trig.trigger_type,
                )
                _schedule_all_notifications(
                    email_service=email_service,
                    user_email=user.email,
                    telegram_id=user.telegram_id,
                    url=tracker.url,
                    old_value=_fmt(trig.trigger_value),
                    new_value=_fmt(new_price),
                    trigger_type=trig.trigger_type,
                    tracker_id=tracker_id,
                )
                fired_trigger_ids.append(trig.id)
            # any_change (price-based)
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
                    _schedule_all_notifications(
                        email_service=email_service,
                        user_email=user.email,
                        telegram_id=user.telegram_id,
                        url=tracker.url,
                        old_value=_fmt(old_price),
                        new_value=_fmt(new_price),
                        trigger_type=trig.trigger_type,
                        tracker_id=tracker_id,
                    )
                    fired_trigger_ids.append(trig.id)
            # back_in_stock: availability became True
            elif trig.trigger_type == "back_in_stock":
                new_avail = None if new_data is None else new_data.get("last_availability")
                old_avail = None if existing is None else getattr(existing, "last_availability", None)
                if new_avail is True and (old_avail is False or old_avail is None):
                    logger.info(
                        "Scheduling back_in_stock notification for tracker %s user %s",
                        tracker_id,
                        user.email,
                    )
                    _schedule_all_notifications(
                        email_service=email_service,
                        user_email=user.email,
                        telegram_id=user.telegram_id,
                        url=tracker.url,
                        old_value=_fmt(trig.trigger_value),
                        new_value=_fmt(new_price),
                        trigger_type=trig.trigger_type,
                        tracker_id=tracker_id,
                    )
                    fired_trigger_ids.append(trig.id)
            # discount threshold
            elif trig.trigger_type == "discount":
                new_disc = None if new_data is None else new_data.get("last_discount_percent")
                if new_disc is not None and trig.trigger_value is not None and new_disc >= trig.trigger_value:
                    logger.info(
                        "Scheduling discount notification for tracker %s user %s",
                        tracker_id,
                        user.email,
                    )
                    _schedule_all_notifications(
                        email_service=email_service,
                        user_email=user.email,
                        telegram_id=user.telegram_id,
                        url=tracker.url,
                        old_value=_fmt(trig.trigger_value),
                        new_value=_fmt(new_disc),
                        trigger_type=trig.trigger_type,
                        tracker_id=tracker_id,
                    )
                    fired_trigger_ids.append(trig.id)
            # cashback reach
            elif trig.trigger_type == "cashback_reach":
                new_cash = None if new_data is None else new_data.get("last_cashback_amount")
                if new_cash is not None and trig.trigger_value is not None and new_cash >= trig.trigger_value:
                    logger.info(
                        "Scheduling cashback_reach notification for tracker %s user %s",
                        tracker_id,
                        user.email,
                    )
                    _schedule_all_notifications(
                        email_service=email_service,
                        user_email=user.email,
                        telegram_id=user.telegram_id,
                        url=tracker.url,
                        old_value=_fmt(trig.trigger_value),
                        new_value=_fmt(new_cash),
                        trigger_type=trig.trigger_type,
                        tracker_id=tracker_id,
                    )
                    fired_trigger_ids.append(trig.id)
            # boolean availability-type triggers (trade_in, credit, gift_offer, personal_price)
            elif trig.trigger_type in ("trade_in_available", "credit_available", "gift_offer_available", "personal_price_available"):
                field_map = {
                    "trade_in_available": "last_trade_in_available",
                    "credit_available": "last_credit_available",
                    "gift_offer_available": "last_gift_offer_available",
                    "personal_price_available": "last_personal_price_available",
                }
                new_flag = None if new_data is None else new_data.get(field_map.get(trig.trigger_type))
                old_flag = None if existing is None else getattr(existing, field_map.get(trig.trigger_type), None)
                if new_flag is True and (old_flag is False or old_flag is None):
                    logger.info(
                        "Scheduling %s notification for tracker %s user %s",
                        trig.trigger_type,
                        tracker_id,
                        user.email,
                    )
                    _schedule_all_notifications(
                        email_service=email_service,
                        user_email=user.email,
                        telegram_id=user.telegram_id,
                        url=tracker.url,
                        old_value=_fmt(trig.trigger_value),
                        new_value=_fmt(new_price),
                        trigger_type=trig.trigger_type,
                        tracker_id=tracker_id,
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
    last_cashback_amount: float | None = None
    last_trade_in_available: bool | None = None
    last_credit_available: bool | None = None
    last_gift_offer_available: bool | None = None
    last_personal_price_available: bool | None = None
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
    existing_before = _snapshot_for_trigger_eval(existing)
    
    if existing:
        existing.last_price = data.last_price
        existing.last_old_price = data.last_old_price
        existing.last_discount_percent = data.last_discount_percent
        existing.last_status = data.last_status
        existing.last_availability = data.last_availability
        existing.last_rating = data.last_rating
        existing.last_views = data.last_views
        existing.last_reviews_count = data.last_reviews_count
        existing.last_cashback_amount = data.last_cashback_amount
        existing.last_trade_in_available = data.last_trade_in_available
        existing.last_credit_available = data.last_credit_available
        existing.last_gift_offer_available = data.last_gift_offer_available
        existing.last_personal_price_available = data.last_personal_price_available
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
            last_cashback_amount=data.last_cashback_amount,
            last_trade_in_available=data.last_trade_in_available,
            last_credit_available=data.last_credit_available,
            last_gift_offer_available=data.last_gift_offer_available,
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
        existing=existing_before,
        new_data=data.model_dump(),
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
    existing_before = _snapshot_for_trigger_eval(existing)
    
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
        existing=existing_before,
        new_data=data.model_dump(),
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
    existing_before = _snapshot_for_trigger_eval(existing)
    
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
        existing=existing_before,
        new_data=data.model_dump(),
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
    last_gift_offer_available: bool | None = None
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
    existing_before = _snapshot_for_trigger_eval(existing)
    
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
            last_gift_offer_available=data.last_gift_offer_available,
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
        existing=existing_before,
        new_data=data.model_dump(),
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
    last_views: int | None = None
    last_cashback_amount: float | None = None
    last_personal_price_available: bool | None = None
    last_trade_in_available: bool | None = None
    last_credit_available: bool | None = None
    last_gift_offer_available: bool | None = None
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
    existing_before = _snapshot_for_trigger_eval(existing)
    
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
            last_views=data.last_views,
            last_cashback_amount=data.last_cashback_amount,
            last_personal_price_available=data.last_personal_price_available,
            last_trade_in_available=data.last_trade_in_available,
            last_credit_available=data.last_credit_available,
            last_gift_offer_available=data.last_gift_offer_available,
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
        existing=existing_before,
        new_data=data.model_dump(),
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
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Comfy offers parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")

    existing_stmt = select(ComfyOffersData).where(
        ComfyOffersData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    old_price = existing.last_price if existing else None
    existing_before = _snapshot_for_trigger_eval(existing)
    
    if existing:
        existing.last_price = data.last_price
        existing.last_old_price = data.last_old_price
        existing.last_discount_percent = data.last_discount_percent
        existing.last_cashback_amount = data.last_cashback_amount
        existing.last_reviews_count = data.last_reviews_count
        existing.last_views = data.last_views
        existing.last_personal_price_available = data.last_personal_price_available
        existing.last_gift_offer_available = data.last_gift_offer_available
        existing.last_color = data.last_color
        existing.last_memory_variant = data.last_memory_variant
        existing.last_checked_at = _parse_iso_datetime(data.last_checked_at)
    else:
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
    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
        existing=existing_before,
        new_data=data.model_dump(),
    )
    return {"status": "ok"}


class FoxtrotWebhookData(BaseModel):
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_status: str | None = None
    last_availability: bool | None = None
    last_rating: float | None = None
    last_reviews_count: int | None = None
    last_views: int | None = None
    last_cashback_amount: float | None = None
    last_trade_in_available: bool | None = None
    last_credit_available: bool | None = None
    last_gift_offer_available: bool | None = None
    last_personal_price_available: bool | None = None
    last_color: str | None = None
    last_memory_variant: str | None = None
    last_delivery_available: bool | None = None
    last_pickup_available: bool | None = None
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
    existing_before = _snapshot_for_trigger_eval(existing)
    
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
            last_views=data.last_views,
            last_cashback_amount=data.last_cashback_amount,
            last_trade_in_available=data.last_trade_in_available,
            last_credit_available=data.last_credit_available,
            last_gift_offer_available=data.last_gift_offer_available,
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
        existing=existing_before,
        new_data=data.model_dump(),
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
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
):
    """Foxtrot offers parser webhook"""
    tracker_stmt = select(ProductTracker).where(ProductTracker.id == tracker_id)
    result = await db.execute(tracker_stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")

    existing_stmt = select(FoxtrotOffersData).where(
        FoxtrotOffersData.tracker_id == tracker_id
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()
    old_price = existing.last_price if existing else None
    existing_before = _snapshot_for_trigger_eval(existing)
    
    if existing:
        existing.last_price = data.last_price
        existing.last_old_price = data.last_old_price
        existing.last_discount_percent = data.last_discount_percent
        existing.last_cashback_amount = data.last_cashback_amount
        existing.last_reviews_count = data.last_reviews_count
        existing.last_views = data.last_views
        existing.last_personal_price_available = data.last_personal_price_available
        existing.last_gift_offer_available = data.last_gift_offer_available
        existing.last_color = data.last_color
        existing.last_memory_variant = data.last_memory_variant
        existing.last_checked_at = _parse_iso_datetime(data.last_checked_at)
    else:
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
    await _evaluate_triggers_and_notify(
        db=db,
        email_service=email_service,
        tracker_id=tracker_id,
        old_price=old_price,
        new_price=data.last_price,
        existing=existing_before,
        new_data=data.model_dump(),
    )
    return {"status": "ok"}
