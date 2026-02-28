import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.staff import Staff
from app.models.user_permission import UserPermission

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "biblioteka-jwt-secret-key-2026-change-me")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
EXPIRATION_MINUTES = int(os.environ.get("JWT_EXPIRATION_MINUTES", "30"))  # Match frontend session timeout

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=EXPIRATION_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Staff:
    token = None
    if credentials:
        token = credentials.credentials
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Niste prijavljeni")

    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nevažeći token")
        user_id = int(user_id_str)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nevažeći token")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nevažeći token")

    user = db.query(Staff).filter(Staff.id == user_id, Staff.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Korisnik nije aktivan")
    return user


def require_admin(current_user: Staff = Depends(get_current_user)) -> Staff:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Samo administrator")
    return current_user


def check_permission(module: str, write: bool = False):
    def _checker(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
        if current_user.is_admin:
            return current_user
        perm = db.query(UserPermission).filter(
            UserPermission.user_id == current_user.id,
            UserPermission.module == module,
        ).first()
        if not perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemate pristup")
        if write and not perm.can_write:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemate dozvolu za izmene")
        if not perm.can_read:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nemate pristup")
        return current_user
    return _checker
