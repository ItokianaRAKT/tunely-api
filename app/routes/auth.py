from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import create_access_token, get_current_user, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, User as UserSchema, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserSchema, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(
        select(User).where((User.email == data.email) | (User.username == data.username))
    )
    if existing:
        if existing.email == data.email:
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserSchema)
def me(current_user: User = Depends(get_current_user)):
    return current_user
