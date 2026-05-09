"""Telegram integration endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services import telegram_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/telegram")


class LinkCodeResponse(BaseModel):
    code: str
    ttl_minutes: int
    bot_username: str | None = None


class TelegramStatusResponse(BaseModel):
    linked: bool
    telegram_username: str | None = None


@router.post("/link-code", response_model=LinkCodeResponse, summary="Generate a Telegram link code")
async def generate_link_code(
    current_user: User = Depends(get_current_user),
) -> LinkCodeResponse:
    """
    Generate a short-lived code the user can send to the Telegram bot via
    `/link CODE` or the deep-link `t.me/<bot>?start=link_CODE` to connect
    their Telegram account.
    """
    code = await telegram_service.generate_link_code(current_user.id)
    return LinkCodeResponse(
        code=code,
        ttl_minutes=settings.telegram_link_code_ttl_minutes,
        bot_username=settings.telegram_bot_username,
    )


@router.delete("/unlink", status_code=status.HTTP_204_NO_CONTENT, summary="Unlink Telegram account")
async def unlink_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove the Telegram link from the current user's account."""
    if current_user.telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram не прив'язаний до цього акаунту.",
        )
    repo = UserRepository(db)
    await repo.clear_telegram(current_user)


@router.get("/status", response_model=TelegramStatusResponse, summary="Check Telegram link status")
async def telegram_status(
    current_user: User = Depends(get_current_user),
) -> TelegramStatusResponse:
    return TelegramStatusResponse(
        linked=current_user.telegram_id is not None,
        telegram_username=current_user.telegram_username,
    )
