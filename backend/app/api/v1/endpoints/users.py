from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.patch("/me", response_model=UserRead)
async def update_user_me(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    
    if user_in.email is not None:
        if user_in.email != current_user.email:
            stmt = select(User).where(User.email == user_in.email)
            result = await db.execute(stmt)
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Цей email вже використовується іншим користувачем",
                )
            current_user.email = user_in.email
            # У реальному проекті тут варто було б знову скинути is_email_verified і надіслати код
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
