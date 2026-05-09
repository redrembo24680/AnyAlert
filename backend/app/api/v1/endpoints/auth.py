from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from jose import JWTError, jwt

from app.api.deps import ensure_guest
from app.dependencies import get_auth_service, get_email_service
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.core.config import settings
from app.api.deps import get_db
from app.repositories.user_repository import UserRepository
from app.core.security import create_access_token, hash_password
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import hmac
import secrets
import time

router = APIRouter(prefix="/auth")


# ──────────────────────────────────────────────────────────────────
# Telegram Login Widget auth
# ──────────────────────────────────────────────────────────────────

class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


def _verify_telegram_auth(data: TelegramAuthData) -> bool:
    """Verify Telegram Login Widget data using HMAC-SHA256."""
    if not settings.telegram_bot_token:
        return False
    # Auth date must be within 24 hours
    if abs(time.time() - data.auth_date) > 86400:
        return False
    fields = {
        "id": str(data.id),
        "first_name": data.first_name,
        "auth_date": str(data.auth_date),
    }
    if data.last_name:
        fields["last_name"] = data.last_name
    if data.username:
        fields["username"] = data.username
    if data.photo_url:
        fields["photo_url"] = data.photo_url
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hashlib.sha256(settings.telegram_bot_token.encode()).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_hash, data.hash)


@router.post("/telegram", response_model=LoginResponse, summary="Login or register via Telegram Widget")
async def telegram_login(
    payload: TelegramAuthData,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    if not _verify_telegram_auth(payload):
        raise HTTPException(status_code=400, detail="Невірний підпис Telegram. Спробуйте ще раз.")

    repo = UserRepository(db)
    user = await repo.get_by_telegram_id(payload.id)

    if user is None:
        # Try to find by generated email (if previously registered via Telegram)
        fake_email = f"telegram_{payload.id}@telegram.user"
        user = await repo.get_by_email(fake_email)

    if user is None:
        # Create new user from Telegram data
        full_name = payload.first_name
        if payload.last_name:
            full_name += f" {payload.last_name}"
        fake_email = f"telegram_{payload.id}@telegram.user"
        user = await repo.create(
            email=fake_email,
            full_name=full_name,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            email_verification_code=None,
            email_verification_expires_at=None,
            is_email_verified=True,
        )

    # Always sync telegram_id / username
    if user.telegram_id != payload.id or user.telegram_username != payload.username:
        await repo.set_telegram(user, payload.id, payload.username)

    await repo.update_last_login(user)

    token = create_access_token(str(user.id))
    return LoginResponse(
        token=token,
        user=LoginResponse.UserPayload(
            name=user.full_name or "",
            email=user.email,
        ),
    )



@router.post("/register", response_model=RegisterResponse, summary="Register a user")
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service),
    _: None = Depends(ensure_guest),
) -> RegisterResponse:
    user = await auth_service.register(payload)

    # Schedule the 6-digit code email that matches the current verification flow.
    background_tasks.add_task(
        email_service.send_verification_code,
        user.email,
        user.email_verification_code,
    )

    return RegisterResponse(
        message="Verification code sent",
        verification_required=True,
        dev_verification_code=user.email_verification_code if settings.debug else None,
    )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify email with 6-digit code",
)
async def verify_email(
    payload: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
    _: None = Depends(ensure_guest),
) -> VerifyEmailResponse:
    login_response = await auth_service.verify_email(email=payload.email, code=payload.code)
    return VerifyEmailResponse(
        message="Email успішно підтверджено",
        token=login_response.token,
        user=login_response.user,
    )


@router.get("/verify", summary="Verify email via token")
async def verify_token(token: str, auth_service: AuthService = Depends(get_auth_service)) -> VerifyEmailResponse:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await auth_service.user_repository.get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await auth_service.user_repository.mark_email_verified(user)
    await auth_service.user_repository.update_last_login(user)
    token = jwt.encode({"sub": str(user.id)}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return VerifyEmailResponse(
        message="Email успішно підтверджено",
        token=token,
        user=LoginResponse.UserPayload(name=user.full_name or "", email=user.email),
    )


@router.post("/login", response_model=LoginResponse, summary="Login user")
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    _: None = Depends(ensure_guest),
) -> LoginResponse:
    return await auth_service.login(payload)
