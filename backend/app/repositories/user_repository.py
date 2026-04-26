from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        email_verification_code: str,
        email_verification_expires_at: datetime,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            email_verification_code=email_verification_code,
            email_verification_expires_at=email_verification_expires_at,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def mark_email_verified(self, user: User) -> User:
        user.is_email_verified = True
        user.email_verification_code = None
        user.email_verification_expires_at = None
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(user)
        return user
