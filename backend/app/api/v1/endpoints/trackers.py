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
    stmt = select(ProductTracker).where(ProductTracker.user_id == current_user.id)
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
    stmt = select(ProductTracker).options(joinedload(ProductTracker.user)).where(ProductTracker.id == tracker_id)
    result = await db.execute(stmt)
    tracker = result.scalars().first()
    
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
        
    old_price = tracker.last_price
    old_status = tracker.last_status
    
    if update_data.title:
        tracker.title = update_data.title
    tracker.last_price = update_data.last_price
    tracker.last_status = update_data.last_status
    tracker.last_checked_at = update_data.last_checked_at
    
    await db.commit()
    
    email_service = EmailService()
    trigger_fired = False
    old_val_str = ""
    new_val_str = ""
    
    # Check triggers
    if tracker.trigger_type == "price_drop" and update_data.last_price is not None and tracker.trigger_value is not None:
        if update_data.last_price <= tracker.trigger_value and (old_price is None or old_price > tracker.trigger_value):
            trigger_fired = True
            old_val_str = f"{old_price} грн" if old_price else "невідомо"
            new_val_str = f"{update_data.last_price} грн"
            
    elif tracker.trigger_type == "in_stock" and update_data.last_status:
        in_stock_keywords = ["в наявності", "є в наявності", "готовий до відправлення"]
        is_now_in_stock = any(kw in update_data.last_status.lower() for kw in in_stock_keywords)
        was_in_stock = old_status and any(kw in old_status.lower() for kw in in_stock_keywords)
        
        if is_now_in_stock and not was_in_stock:
            trigger_fired = True
            old_val_str = old_status or "невідомо"
            new_val_str = update_data.last_status
            
    elif tracker.trigger_type == "any_change":
        if (old_price != update_data.last_price) or (old_status != update_data.last_status):
            if old_price is not None or old_status is not None: # Don't trigger on the very first parse
                trigger_fired = True
                old_val_str = f"Ціна: {old_price}, Статус: {old_status}"
                new_val_str = f"Ціна: {update_data.last_price}, Статус: {update_data.last_status}"

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

