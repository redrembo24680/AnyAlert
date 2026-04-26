from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=255)


class RegisterResponse(BaseModel):
    message: str
    verification_required: bool = True
    dev_verification_code: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=255)


class LoginResponse(BaseModel):
    token: str

    class UserPayload(BaseModel):
        name: str
        email: EmailStr

    user: UserPayload


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class VerifyEmailResponse(BaseModel):
    message: str
    token: str
    user: LoginResponse.UserPayload
