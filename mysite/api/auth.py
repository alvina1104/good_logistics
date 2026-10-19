from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from mysite.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
from mysite.database.db import get_db
from mysite.database.models import User, RefreshToken, RoleChoices
from mysite.database.schema import UserCreateSchema, UserLoginSchema, UserOutSchema

credentials_exception = HTTPException(status_code=401, detail="Не удалось проверить учетные данные", headers={"WWW-Authenticate": "Bearer"})
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/")
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_LIFETIME)), "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_LIFETIME), "token_type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_token_data(user: User):
    return {"sub": str(user.id), "username": user.username, "status": user.status.value}


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type") != "access":
            raise credentials_exception
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    return user


@auth_router.post("/register/")
async def register(user: UserCreateSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username уже существует")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email уже существует")
    user_data = User(username=user.username, email=user.email, password=get_password_hash(user.password), status=RoleChoices.buyer)
    db.add(user_data)
    db.commit()
    db.refresh(user_data)
    return {"message": "Вы успешно создали аккаунт"}


@auth_router.post("/login/")
async def login(data: UserLoginSchema, db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.username == data.username).first()
    if not user_db or not verify_password(data.password, user_db.password):
        raise HTTPException(status_code=401, detail="Username или password неправильный")
    token_data = get_token_data(user_db)
    access_token, refresh_token = create_access_token(token_data), create_refresh_token(token_data)
    db.add(RefreshToken(user_id=user_db.id, token=refresh_token, expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_LIFETIME)))
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "Bearer"}


@auth_router.post("/logout/")
async def logout(refresh_token: str = Query(...), db: Session = Depends(get_db)):
    token_db = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not token_db:
        raise HTTPException(status_code=401, detail="Неверный refresh token")
    db.delete(token_db)
    db.commit()
    return {"message": "Пользователь успешно вышел из системы"}


@auth_router.post("/refresh/")
async def refresh(refresh_token: str = Query(...), db: Session = Depends(get_db)):
    token_db = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not token_db or token_db.expires_at <= datetime.utcnow():
        if token_db:
            db.delete(token_db)
            db.commit()
        raise HTTPException(status_code=401, detail="Refresh token недействителен или истёк")
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type") != "refresh":
            raise credentials_exception
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Refresh token недействителен или истёк")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or token_db.user_id != user.id:
        raise credentials_exception
    access_token = create_access_token(get_token_data(user))
    return {"access_token": access_token, "token_type": "Bearer"}


@auth_router.get("/me/", response_model=UserOutSchema)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
