from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register(self, payload: UserCreate):
        existing = await self.user_repository.get_by_email(payload.email)
        if existing:
            raise ValueError("User with this email already exists")

        return await self.user_repository.create(payload)
