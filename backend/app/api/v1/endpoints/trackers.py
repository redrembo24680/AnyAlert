from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.tracker import ProductTracker
from app.schemas.tracker import TrackerCreate, TrackerResponse, TrackerUpdate
from app.services.email_service import EmailService

router = APIRouter()


@router.get("/active", response_model=list[TrackerResponse])
async def get_active_trackers(db: AsyncSession = Depends(get_db)):
    """
    Get all active trackers for the parser.
    """
    stmt = select(ProductTracker).where(ProductTracker.is_active == True)
    result = await db.execute(stmt)
    trackers = result.scalars().all()
    return trackers


@router.get("/", response_model=list[TrackerResponse])
async def get_my_trackers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all trackers for the current user.
    """
    stmt = select(ProductTracker).where(
        ProductTracker.user_id == current_user.id)
    result = await db.execute(stmt)
    trackers = result.scalars().all()
    return trackers


@router.post("/", response_model=TrackerResponse)
async def create_tracker(
    tracker_in: TrackerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new product tracker for the current user.
    """
    # Avoid duplicate active trackers for the same condition.
    same_tracker_stmt = select(ProductTracker).where(
        ProductTracker.user_id == current_user.id,
        ProductTracker.url == tracker_in.url,
        ProductTracker.network == tracker_in.network,
        ProductTracker.trigger_type == tracker_in.trigger_type,
        ProductTracker.trigger_value == tracker_in.trigger_value,
    )
    existing_result = await db.execute(same_tracker_stmt)
    existing_trackers = existing_result.scalars().all()

    active_tracker = next((t for t in existing_trackers if t.is_active), None)
    if active_tracker is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такий активний тригер уже існує",
        )

    inactive_tracker = next(
        (t for t in existing_trackers if not t.is_active), None)
    if inactive_tracker is not None:
        # Reactivate old tracker and reset last parsed snapshot so it starts fresh.
        inactive_tracker.is_active = True
        inactive_tracker.last_price = None
        inactive_tracker.last_old_price = None
        inactive_tracker.last_discount_percent = None
        inactive_tracker.last_rating = None
        inactive_tracker.last_views = None
        inactive_tracker.last_reviews_count = None
        inactive_tracker.last_cashback_amount = None
        inactive_tracker.last_trade_in_available = None
        inactive_tracker.last_credit_available = None
        inactive_tracker.last_color = None
        inactive_tracker.last_memory_variant = None
        inactive_tracker.last_delivery_available = None
        inactive_tracker.last_pickup_available = None
        inactive_tracker.last_personal_price_available = None
        inactive_tracker.last_gift_offer_available = None
        inactive_tracker.last_availability = None
        inactive_tracker.last_status = None
        inactive_tracker.last_checked_at = None

        await db.commit()
        await db.refresh(inactive_tracker)
        return inactive_tracker

    tracker = ProductTracker(
        **tracker_in.model_dump(),
        user_id=current_user.id
    )
    db.add(tracker)
    await db.commit()
    await db.refresh(tracker)
    return tracker


@router.post("/{tracker_id}/webhook", status_code=status.HTTP_200_OK)
async def update_tracker_from_parser(
    tracker_id: int,
    update_data: TrackerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook for the parser to update the tracker data.
    """
    stmt = select(ProductTracker).options(joinedload(
        ProductTracker.user)).where(ProductTracker.id == tracker_id)
    result = await db.execute(stmt)
    tracker = result.scalars().first()

    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")

    old_price = tracker.last_price
    old_discount = tracker.last_discount_percent
    old_rating = tracker.last_rating
    old_views = tracker.last_views
    old_reviews_count = tracker.last_reviews_count
    old_cashback_amount = tracker.last_cashback_amount
    old_trade_in_available = tracker.last_trade_in_available
    old_credit_available = tracker.last_credit_available
    old_color = tracker.last_color
    old_memory_variant = tracker.last_memory_variant
    old_delivery_available = tracker.last_delivery_available
    old_pickup_available = tracker.last_pickup_available
    old_personal_price_available = tracker.last_personal_price_available
    old_gift_offer_available = tracker.last_gift_offer_available
    old_availability = tracker.last_availability
    old_status = tracker.last_status

    if update_data.title:
        tracker.title = update_data.title
    tracker.last_price = update_data.last_price
    tracker.last_old_price = update_data.last_old_price
    tracker.last_discount_percent = update_data.last_discount_percent
    tracker.last_rating = update_data.last_rating
    tracker.last_views = update_data.last_views
    tracker.last_reviews_count = update_data.last_reviews_count
    tracker.last_cashback_amount = update_data.last_cashback_amount
    tracker.last_trade_in_available = update_data.last_trade_in_available
    tracker.last_credit_available = update_data.last_credit_available
    tracker.last_color = update_data.last_color
    tracker.last_memory_variant = update_data.last_memory_variant
    tracker.last_delivery_available = update_data.last_delivery_available
    tracker.last_pickup_available = update_data.last_pickup_available
    tracker.last_personal_price_available = update_data.last_personal_price_available
    tracker.last_gift_offer_available = update_data.last_gift_offer_available
    tracker.last_availability = update_data.last_availability
    tracker.last_status = update_data.last_status
    tracker.last_checked_at = update_data.last_checked_at

    await db.commit()

    email_service = EmailService()
    trigger_fired = False
    old_val_str = ""
    new_val_str = ""

    # Check triggers
    if tracker.trigger_type in {"price_drop", "price_below"} and update_data.last_price is not None and tracker.trigger_value is not None:
        if update_data.last_price <= tracker.trigger_value and (old_price is None or old_price > tracker.trigger_value):
            trigger_fired = True
            old_val_str = f"{old_price} грн" if old_price else "невідомо"
            new_val_str = f"{update_data.last_price} грн"

    elif tracker.trigger_type == "price_rise" and update_data.last_price is not None and tracker.trigger_value is not None:
        if update_data.last_price >= tracker.trigger_value and (old_price is None or old_price < tracker.trigger_value):
            trigger_fired = True
            old_val_str = f"{old_price} грн" if old_price else "невідомо"
            new_val_str = f"{update_data.last_price} грн"

    elif tracker.trigger_type == "discount" and update_data.last_discount_percent is not None and tracker.trigger_value is not None:
        if update_data.last_discount_percent >= tracker.trigger_value and (old_discount is None or old_discount < tracker.trigger_value):
            trigger_fired = True
            old_val_str = f"{old_discount}%" if old_discount is not None else "невідомо"
            new_val_str = f"{update_data.last_discount_percent}%"

    elif tracker.trigger_type == "rating_drop" and update_data.last_rating is not None and tracker.trigger_value is not None:
        if update_data.last_rating <= tracker.trigger_value and (old_rating is None or old_rating > tracker.trigger_value):
            trigger_fired = True
            old_val_str = f"{old_rating}" if old_rating is not None else "невідомо"
            new_val_str = f"{update_data.last_rating}"

    elif tracker.trigger_type == "views_reach" and update_data.last_views is not None and tracker.trigger_value is not None:
        threshold = int(tracker.trigger_value)
        if update_data.last_views >= threshold and (old_views is None or old_views < threshold):
            trigger_fired = True
            old_val_str = f"{old_views}" if old_views is not None else "невідомо"
            new_val_str = f"{update_data.last_views}"

    elif tracker.trigger_type == "reviews_reach" and update_data.last_reviews_count is not None and tracker.trigger_value is not None:
        threshold = int(tracker.trigger_value)
        if update_data.last_reviews_count >= threshold and (old_reviews_count is None or old_reviews_count < threshold):
            trigger_fired = True
            old_val_str = f"{old_reviews_count}" if old_reviews_count is not None else "невідомо"
            new_val_str = f"{update_data.last_reviews_count}"

    elif tracker.trigger_type == "cashback_reach" and update_data.last_cashback_amount is not None and tracker.trigger_value is not None:
        if update_data.last_cashback_amount >= tracker.trigger_value and (old_cashback_amount is None or old_cashback_amount < tracker.trigger_value):
            trigger_fired = True
            old_val_str = f"{old_cashback_amount} ₴" if old_cashback_amount is not None else "невідомо"
            new_val_str = f"{update_data.last_cashback_amount} ₴"

    elif tracker.trigger_type == "trade_in_available" and update_data.last_trade_in_available is not None:
        if old_trade_in_available is not None and update_data.last_trade_in_available and not old_trade_in_available:
            trigger_fired = True
            old_val_str = "Немає"
            new_val_str = "Є"

    elif tracker.trigger_type == "credit_available" and update_data.last_credit_available is not None:
        if old_credit_available is not None and update_data.last_credit_available and not old_credit_available:
            trigger_fired = True
            old_val_str = "Немає"
            new_val_str = "Є"

    elif tracker.trigger_type == "delivery_available" and update_data.last_delivery_available is not None:
        if old_delivery_available is not None and update_data.last_delivery_available and not old_delivery_available:
            trigger_fired = True
            old_val_str = "Немає"
            new_val_str = "Є"

    elif tracker.trigger_type == "pickup_available" and update_data.last_pickup_available is not None:
        if old_pickup_available is not None and update_data.last_pickup_available and not old_pickup_available:
            trigger_fired = True
            old_val_str = "Немає"
            new_val_str = "Є"

    elif tracker.trigger_type == "personal_price_available" and update_data.last_personal_price_available is not None:
        if old_personal_price_available is not None and update_data.last_personal_price_available and not old_personal_price_available:
            trigger_fired = True
            old_val_str = "Немає"
            new_val_str = "Є"

    elif tracker.trigger_type == "gift_offer_available" and update_data.last_gift_offer_available is not None:
        if old_gift_offer_available is not None and update_data.last_gift_offer_available and not old_gift_offer_available:
            trigger_fired = True
            old_val_str = "Немає"
            new_val_str = "Є"

    elif tracker.trigger_type == "color_change" and update_data.last_color:
        if old_color is not None and old_color != update_data.last_color:
            trigger_fired = True
            old_val_str = old_color
            new_val_str = update_data.last_color

    elif tracker.trigger_type == "memory_variant_change" and update_data.last_memory_variant:
        if old_memory_variant is not None and old_memory_variant != update_data.last_memory_variant:
            trigger_fired = True
            old_val_str = old_memory_variant
            new_val_str = update_data.last_memory_variant

    elif tracker.trigger_type in {"in_stock", "back_in_stock"} and (update_data.last_status or update_data.last_availability is not None):
        in_stock_keywords = ["в наявності", "є в наявності",
                             "готовий до відправлення", "available"]
        is_now_in_stock = (
            update_data.last_availability
            if update_data.last_availability is not None
            else any(kw in update_data.last_status.lower() for kw in in_stock_keywords)
        )
        was_in_stock = (
            old_availability
            if old_availability is not None
            else bool(old_status and any(kw in old_status.lower() for kw in in_stock_keywords))
        )

        if is_now_in_stock and not was_in_stock:
            trigger_fired = True
            old_val_str = old_status or "невідомо"
            new_val_str = update_data.last_status

    elif tracker.trigger_type == "any_change":
        if (
            (old_price != update_data.last_price)
            or (old_status != update_data.last_status)
            or (old_discount != update_data.last_discount_percent)
            or (old_rating != update_data.last_rating)
            or (old_views != update_data.last_views)
            or (old_reviews_count != update_data.last_reviews_count)
            or (old_cashback_amount != update_data.last_cashback_amount)
            or (old_trade_in_available != update_data.last_trade_in_available)
            or (old_credit_available != update_data.last_credit_available)
            or (old_color != update_data.last_color)
            or (old_memory_variant != update_data.last_memory_variant)
            or (old_delivery_available != update_data.last_delivery_available)
            or (old_pickup_available != update_data.last_pickup_available)
            or (old_personal_price_available != update_data.last_personal_price_available)
            or (old_gift_offer_available != update_data.last_gift_offer_available)
            or (old_availability != update_data.last_availability)
        ):
            if old_price is not None or old_status is not None or old_discount is not None or old_rating is not None or old_views is not None or old_reviews_count is not None or old_cashback_amount is not None or old_trade_in_available is not None or old_credit_available is not None or old_color is not None or old_memory_variant is not None or old_delivery_available is not None or old_pickup_available is not None or old_personal_price_available is not None or old_gift_offer_available is not None or old_availability is not None:
                trigger_fired = True
                old_val_str = (
                    f"Ціна: {old_price}, Статус: {old_status}, Знижка: {old_discount}, "
                    f"Рейтинг: {old_rating}, Перегляди: {old_views}, Відгуки: {old_reviews_count}, "
                    f"Кешбек: {old_cashback_amount}, Trade-in: {old_trade_in_available}, "
                    f"Кредит: {old_credit_available}, Доставка: {old_delivery_available}, "
                    f"Самовивіз: {old_pickup_available}, Персональна ціна: {old_personal_price_available}, "
                    f"Подарунок: {old_gift_offer_available}, Колір: {old_color}, Пам'ять: {old_memory_variant}, "
                    f"Наявність: {old_availability}"
                )
                new_val_str = (
                    f"Ціна: {update_data.last_price}, Статус: {update_data.last_status}, "
                    f"Знижка: {update_data.last_discount_percent}, Рейтинг: {update_data.last_rating}, "
                    f"Перегляди: {update_data.last_views}, Відгуки: {update_data.last_reviews_count}, "
                    f"Кешбек: {update_data.last_cashback_amount}, Trade-in: {update_data.last_trade_in_available}, "
                    f"Кредит: {update_data.last_credit_available}, Доставка: {update_data.last_delivery_available}, "
                    f"Самовивіз: {update_data.last_pickup_available}, Персональна ціна: {update_data.last_personal_price_available}, "
                    f"Подарунок: {update_data.last_gift_offer_available}, Колір: {update_data.last_color}, "
                    f"Пам'ять: {update_data.last_memory_variant}, Наявність: {update_data.last_availability}"
                )

    if trigger_fired and tracker.user and tracker.user.email:
        try:
            await email_service.send_trigger_notification(
                recipient_email=tracker.user.email,
                url=tracker.url,
                old_value=old_val_str,
                new_value=new_val_str,
                trigger_type=tracker.trigger_type,
                title=tracker.title
            )
            # Disable tracker after triggering
            tracker.is_active = False
            await db.commit()
        except Exception as e:
            print(f"Failed to send email notification: {e}")

    return {"status": "ok"}


@router.delete("/{tracker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracker(
    tracker_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a product tracker.
    """
    stmt = select(ProductTracker).where(
        ProductTracker.id == tracker_id,
        ProductTracker.user_id == current_user.id
    )
    result = await db.execute(stmt)
    tracker = result.scalars().first()

    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")

    await db.delete(tracker)
    await db.commit()
    return None
