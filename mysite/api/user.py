from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.api.auth import get_current_user, get_password_hash
from mysite.database.db import get_db
from mysite.database.models import User, RoleChoices
from mysite.database.schema import UserOutSchema, UserUpdateSchema

user_router = APIRouter(prefix="/users", tags=["Users"])



@user_router.get("/me/", response_model=UserOutSchema)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@user_router.put("/me/", response_model=UserOutSchema)
async def update_my_profile(data: UserUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    values = data.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in values.items():
        if db.query(User).filter(getattr(User, key) == value, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail=f"{key} уже существует")
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@user_router.get("/", response_model=list[UserOutSchema])
async def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager:
        raise HTTPException(status_code=403, detail="Только manager может просматривать пользователей")
    return db.query(User).all()


@user_router.get("/{user_id}", response_model=UserOutSchema)
async def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому пользователю")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user



@user_router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.status != RoleChoices.manager and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к удалению этого пользователя")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"message": "Аккаунт успешно удалён"}
