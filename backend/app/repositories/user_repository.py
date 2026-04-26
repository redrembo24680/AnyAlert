from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, payload: UserCreate) -> User:
        user = User(email=payload.email, full_name=payload.full_name)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
