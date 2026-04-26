from fastapi import APIRouter, Depends

from app.dependencies import get_auth_service
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=RegisterResponse, summary="Register a user")
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await auth_service.register(payload)


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify email with 6-digit code",
)
async def verify_email(
    payload: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> VerifyEmailResponse:
    login_response = await auth_service.verify_email(email=payload.email, code=payload.code)
    return VerifyEmailResponse(
        message="Email успішно підтверджено",
        token=login_response.token,
        user=login_response.user,
    )


@router.post("/login", response_model=LoginResponse, summary="Login user")
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await auth_service.login(payload)
