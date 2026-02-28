from datetime import datetime
import os
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.staff import Staff
from app.schemas.auth import LoginRequest, LoginResponse, StaffCreate, StaffUpdate, StaffOut
from app.utils.auth import (
    verify_password, hash_password, create_access_token,
    get_current_user, require_admin, EXPIRATION_MINUTES,
)
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(Staff).filter(Staff.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Pogrešno korisničko ime ili lozinka")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Nalog je deaktiviran")

    token = create_access_token({"sub": str(user.id)})
    user.last_login = datetime.utcnow()
    db.commit()

    log_activity(db, user.id, "LOGIN", "staff", user.id,
                 ip_address=request.client.host if request.client else None)

    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return LoginResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        is_admin=user.is_admin,
    )


@router.post("/logout")
def logout(request: Request, response: Response, current_user: Staff = Depends(get_current_user),
           db: Session = Depends(get_db)):
    log_activity(db, current_user.id, "LOGOUT", "staff", current_user.id,
                 ip_address=request.client.host if request.client else None)
    response.delete_cookie("access_token")
    return {"message": "Odjavljeni ste"}


@router.get("/me", response_model=StaffOut)
def me(current_user: Staff = Depends(get_current_user)):
    return current_user


@router.get("/config")
def get_config():
    """Get session configuration (timeout in minutes)"""
    session_timeout = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "30"))
    return {"session_timeout_minutes": session_timeout, "session_warning_minutes": 5}


@router.get("/staff", response_model=list[StaffOut])
def list_staff(current_user: Staff = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Staff).all()


@router.post("/staff", response_model=StaffOut)
def create_staff(data: StaffCreate, request: Request,
                 current_user: Staff = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(Staff).filter(Staff.username == data.username).first():
        raise HTTPException(status_code=400, detail="Korisničko ime već postoji")
    user = Staff(
        username=data.username,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        is_admin=data.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_activity(db, current_user.id, "CREATE", "staff", user.id,
                 new_values={"username": user.username, "full_name": user.full_name},
                 ip_address=request.client.host if request.client else None)
    return user


@router.put("/staff/{user_id}", response_model=StaffOut)
def update_staff(user_id: int, data: StaffUpdate, request: Request,
                 current_user: Staff = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(Staff).filter(Staff.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    old_values = {"full_name": user.full_name, "is_admin": user.is_admin, "is_active": user.is_active}
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.is_admin is not None:
        user.is_admin = data.is_admin
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)
    log_activity(db, current_user.id, "UPDATE", "staff", user.id,
                 old_values=old_values,
                 new_values={"full_name": user.full_name, "is_admin": user.is_admin, "is_active": user.is_active},
                 ip_address=request.client.host if request.client else None)
    return user
