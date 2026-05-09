from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.tracker import ProductTracker, ProductTrackerTrigger
from app.schemas.tracker import TrackerCreate, TrackerResponse, TrackerWithTriggersResponse
from app.services.email_service import EmailService

router = APIRouter()


@router.get("/active", response_model=list[TrackerResponse])
async def get_active_trackers(db: AsyncSession = Depends(get_db)):
    """
    Get all active trackers for the parser.
    """
    stmt = select(ProductTracker).join(ProductTrackerTrigger).where(
        ProductTracker.is_active == True,
        ProductTrackerTrigger.is_active == True,
    ).options(
        joinedload(ProductTracker.triggers)
    ).distinct()
    result = await db.execute(stmt)
    trackers = result.unique().scalars().all()
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
        ProductTracker.user_id == current_user.id
    ).options(joinedload(ProductTracker.triggers))
    result = await db.execute(stmt)
    trackers = result.unique().scalars().all()
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
    # Check for duplicate active trackers with same URL and network
    same_tracker_stmt = select(ProductTracker).where(
        ProductTracker.user_id == current_user.id,
        ProductTracker.url == tracker_in.url,
        ProductTracker.network == tracker_in.network,
        ProductTracker.is_active == True
    )
    existing_result = await db.execute(same_tracker_stmt)
    existing_trackers = existing_result.scalars().all()
    if existing_trackers:
        # If a tracker for this URL/network already exists, attach a new trigger
        # unless an identical active trigger is already present.
        tracker_ids = [t.id for t in existing_trackers]

        triggers_stmt = select(ProductTrackerTrigger).where(
            ProductTrackerTrigger.tracker_id.in_(tracker_ids),
            ProductTrackerTrigger.trigger_type == tracker_in.trigger_type,
            ProductTrackerTrigger.is_active == True,
        )
        # match trigger_value explicitly (NULLs included)
        if tracker_in.trigger_value is None:
            triggers_stmt = triggers_stmt.where(ProductTrackerTrigger.trigger_value == None)
        else:
            triggers_stmt = triggers_stmt.where(ProductTrackerTrigger.trigger_value == tracker_in.trigger_value)

        trig_res = await db.execute(triggers_stmt)
        matching_triggers = trig_res.scalars().all()

        if matching_triggers:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Активний тригер того ж типу/значення вже існує для цього URL",
            )

        # Attach new trigger to the first existing tracker
        parent_tracker = existing_trackers[0]
        trigger = ProductTrackerTrigger(
            tracker_id=parent_tracker.id,
            trigger_type=tracker_in.trigger_type,
            trigger_value=tracker_in.trigger_value,
            is_active=True,
        )
        db.add(trigger)
        await db.commit()
        await db.refresh(parent_tracker)
        return parent_tracker

    # No existing active tracker — create the tracker with trigger
    tracker = ProductTracker(
        url=tracker_in.url,
        network=tracker_in.network,
        user_id=current_user.id,
    )
    db.add(tracker)
    await db.flush()  # Get the tracker ID

    # Create the trigger
    trigger = ProductTrackerTrigger(
        tracker_id=tracker.id,
        trigger_type=tracker_in.trigger_type,
        trigger_value=tracker_in.trigger_value,
        is_active=True,
    )
    db.add(trigger)
    await db.commit()
    await db.refresh(tracker)
    return tracker


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
