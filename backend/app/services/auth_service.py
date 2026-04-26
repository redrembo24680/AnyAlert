from datetime import UTC, datetime, timedelta
import logging

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_email_verification_code,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repository: UserRepository, email_service: EmailService) -> None:
        self.user_repository = user_repository
        self.email_service = email_service

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        existing = await self.user_repository.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Користувач з таким email вже існує",
            )

        code = generate_email_verification_code()
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.email_verification_code_ttl_minutes
        )

        await self.user_repository.create(
            email=payload.email,
            full_name=payload.name,
            hashed_password=hash_password(payload.password),
            email_verification_code=code,
            email_verification_expires_at=expires_at,
        )

        if settings.email_enabled:
            try:
                await self.email_service.send_verification_code(payload.email, code)
            except Exception as exc:
                logger.exception("Failed to send verification email", exc_info=exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Не вдалося надіслати лист підтвердження. Спробуйте ще раз.",
                ) from exc

        return RegisterResponse(
            message="Код підтвердження відправлено на email",
            verification_required=True,
            dev_verification_code=code if settings.debug else None,
        )

    async def verify_email(self, email: str, code: str) -> LoginResponse:
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Користувача не знайдено",
            )

        if not user.is_email_verified:
            if not user.email_verification_code or not user.email_verification_expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Код підтвердження недійсний",
                )

            if datetime.now(UTC) > user.email_verification_expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Код підтвердження протермінований",
                )

            if user.email_verification_code != code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Невірний код підтвердження",
                )

            await self.user_repository.mark_email_verified(user)

        await self.user_repository.update_last_login(user)
        token = create_access_token(subject=str(user.id))
        return LoginResponse(
            token=token,
            user=LoginResponse.UserPayload(name=user.full_name or "", email=user.email),
        )

    async def login(self, payload: LoginRequest) -> LoginResponse:
        user = await self.user_repository.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірний email або пароль",
            )

        if not user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Підтвердіть email перед входом",
            )

        await self.user_repository.update_last_login(user)

        token = create_access_token(subject=str(user.id))
        return LoginResponse(
            token=token,
            user=LoginResponse.UserPayload(name=user.full_name or "", email=user.email),
        )
