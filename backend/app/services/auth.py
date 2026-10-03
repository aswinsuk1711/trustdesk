from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Customer, User

_pwd = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your OTP first.")
    return user


def customer_id_for(username: str) -> str:
    return f"CUS-{username}"


def ensure_customer(db: Session, user: User) -> Customer:
    customer = db.get(Customer, customer_id_for(user.username))
    if customer is None:
        customer = Customer(
            id=customer_id_for(user.username),
            name=user.username,
            email=user.email,
            tier="standard",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    return customer


def register_user(db: Session, username: str, email: str, password: str) -> User:
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(username=username, email=email, hashed_password=_pwd.hash(password), role="agent", is_verified=False)
    db.add(user)
    db.add(Customer(id=customer_id_for(username), name=username, email=email, tier="standard"))
    db.commit()
    db.refresh(user)
    return user


def get_current_user(token: str = Depends(_oauth2), db: Session = Depends(get_db)) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exc
    except JWTError:
        raise credentials_exc
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise credentials_exc
    return user
