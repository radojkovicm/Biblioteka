import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.setting import Setting
from app.models.staff import Staff
from app.models.user_permission import UserPermission
from app.schemas.settings import SettingUpdate, PermissionSet, PermissionOut, EmailTestRequest
from app.utils.auth import require_admin, get_current_user
from app.utils.activity_logger import log_activity
from app.utils.i18n import CURRENCIES, LANGUAGES, TRANSLATIONS

router = APIRouter(prefix="/settings", tags=["settings"])

MODULES = ["books", "members", "reservations", "reports", "settings", "finance"]


@router.get("/public/config")
def get_public_config(db: Session = Depends(get_db)):
    """Get public configuration (no auth required)"""
    settings = db.query(Setting).all()
    config = {}
    for s in settings:
        config[s.key] = s.value
    
    return {
        "currency": config.get("currency", "RSD"),
        "language": config.get("language", "sr"),
        "currencies": CURRENCIES,
        "languages": LANGUAGES,
        "translations": TRANSLATIONS.get(config.get("language", "sr"), TRANSLATIONS["sr"]),
        "library_name": config.get("library_name", "Biblioteka"),
    }


@router.get("")
def get_all_settings(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = db.query(Setting).all()
    result = {}
    for s in settings:
        if s.key == "email_smtp_password" and not current_user.is_admin:
            result[s.key] = "********" if s.value else ""
        else:
            result[s.key] = s.value
    return result


@router.put("")
def update_setting(data: SettingUpdate, request: Request,
                   current_user: Staff = Depends(require_admin), db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == data.key).first()
    old_value = setting.value if setting else None
    if setting:
        setting.value = data.value
        setting.updated_at = datetime.utcnow()
        setting.updated_by = current_user.id
    else:
        setting = Setting(key=data.key, value=data.value, updated_by=current_user.id)
        db.add(setting)
    db.commit()
    log_activity(db, current_user.id, "UPDATE", "setting", None,
                 old_values={"key": data.key, "value": old_value},
                 new_values={"key": data.key, "value": data.value if "password" not in data.key else "***"},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Podešavanje sačuvano"}


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...),
                      current_user: Staff = Depends(require_admin), db: Session = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Fajl mora biti slika")
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    logo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "static")
    os.makedirs(logo_dir, exist_ok=True)
    logo_path = os.path.join(logo_dir, f"logo.{ext}")
    content = await file.read()
    with open(logo_path, "wb") as f:
        f.write(content)

    # Save path in settings
    setting = db.query(Setting).filter(Setting.key == "library_logo_path").first()
    if setting:
        setting.value = f"/static/logo.{ext}"
    else:
        db.add(Setting(key="library_logo_path", value=f"/static/logo.{ext}"))
    db.commit()
    return {"message": "Logo sačuvan", "path": f"/static/logo.{ext}"}


# --- Permissions ---

@router.get("/permissions/{user_id}", response_model=list[PermissionOut])
def get_user_permissions(user_id: int, current_user: Staff = Depends(require_admin),
                         db: Session = Depends(get_db)):
    return db.query(UserPermission).filter(UserPermission.user_id == user_id).all()


@router.put("/permissions")
def set_permission(data: PermissionSet, request: Request,
                   current_user: Staff = Depends(require_admin), db: Session = Depends(get_db)):
    if data.module not in MODULES:
        raise HTTPException(status_code=400, detail=f"Nepoznat modul: {data.module}")

    perm = db.query(UserPermission).filter(
        UserPermission.user_id == data.user_id,
        UserPermission.module == data.module,
    ).first()
    if perm:
        perm.can_read = data.can_read
        perm.can_write = data.can_write
    else:
        perm = UserPermission(
            user_id=data.user_id,
            module=data.module,
            can_read=data.can_read,
            can_write=data.can_write,
        )
        db.add(perm)
    db.commit()
    log_activity(db, current_user.id, "UPDATE", "permission", data.user_id,
                 new_values={"module": data.module, "can_read": data.can_read, "can_write": data.can_write},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Dozvola sačuvana"}


# --- Email test ---

@router.post("/email/test")
def test_email(data: EmailTestRequest, current_user: Staff = Depends(require_admin),
               db: Session = Depends(get_db)):
    from app.services.notifications import send_email, get_email_config
    config = get_email_config(db)
    if not config["enabled"]:
        raise HTTPException(status_code=400, detail="Email notifikacije su isključene")

    success, error = send_email(
        config=config,
        to_email=data.to_email,
        subject="Test email — Biblioteka",
        body="Ovo je test email iz sistema za upravljanje bibliotekom.\n\nAko ovo vidite, konfiguracija je ispravna!",
    )
    if success:
        return {"message": f"Test email poslat na {data.to_email}"}
    else:
        raise HTTPException(status_code=500, detail=f"Greška pri slanju: {error}")
