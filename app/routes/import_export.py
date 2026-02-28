import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.staff import Staff
from app.utils.auth import get_current_user, require_admin
from app.utils.activity_logger import log_activity
from app.services.excel import (
    export_books_to_excel, export_members_to_excel,
    import_books_from_excel, import_members_from_excel,
    generate_import_template,
)
from app.services.backup import manual_backup, export_full_database, list_backups

router = APIRouter(tags=["import_export"])


# --- Export ---

@router.get("/export/books")
def export_books(request: Request, current_user: Staff = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    path = export_books_to_excel(db)
    log_activity(db, current_user.id, "EXPORT", "books", ip_address=request.client.host if request.client else None)
    return FileResponse(path, filename="knjige.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/export/members")
def export_members(request: Request, current_user: Staff = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    path = export_members_to_excel(db)
    log_activity(db, current_user.id, "EXPORT", "members", ip_address=request.client.host if request.client else None)
    return FileResponse(path, filename="clanovi.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/export/template/{template_type}")
def download_template(template_type: str, current_user: Staff = Depends(get_current_user)):
    if template_type not in ("books", "members"):
        raise HTTPException(status_code=400, detail="Tip šablona: books ili members")
    path = generate_import_template(template_type)
    return FileResponse(path, filename=f"sablon_{template_type}.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# --- Import ---

@router.post("/import/books")
async def import_books(request: Request, file: UploadFile = File(...),
                       current_user: Staff = Depends(require_admin),
                       db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Fajl mora biti Excel (.xlsx)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = import_books_from_excel(tmp_path, db)
        log_activity(db, current_user.id, "IMPORT", "books",
                     new_values={"imported": result["imported"], "errors_count": len(result.get("errors", []))},
                     ip_address=request.client.host if request.client else None)
        return result
    finally:
        os.unlink(tmp_path)


@router.post("/import/members")
async def import_members(request: Request, file: UploadFile = File(...),
                         current_user: Staff = Depends(require_admin),
                         db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Fajl mora biti Excel (.xlsx)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = import_members_from_excel(tmp_path, db)
        log_activity(db, current_user.id, "IMPORT", "members",
                     new_values={"imported": result["imported"], "errors_count": len(result.get("errors", []))},
                     ip_address=request.client.host if request.client else None)
        return result
    finally:
        os.unlink(tmp_path)


# --- Backup ---

@router.post("/backup/now")
def backup_now(request: Request, current_user: Staff = Depends(require_admin),
               db: Session = Depends(get_db)):
    path = manual_backup()
    log_activity(db, current_user.id, "EXPORT", "backup",
                 new_values={"path": path},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Backup kreiran", "path": path}


@router.get("/backup/list")
def get_backups(current_user: Staff = Depends(require_admin)):
    return list_backups()


@router.get("/backup/download/{filename}")
def download_backup(filename: str, current_user: Staff = Depends(require_admin)):
    from app.services.backup import BACKUP_DIR
    path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Backup fajl nije pronađen")
    return FileResponse(path, filename=filename, media_type="application/octet-stream")


@router.post("/backup/export-full")
def export_full(request: Request, current_user: Staff = Depends(require_admin),
                db: Session = Depends(get_db)):
    path = export_full_database()
    log_activity(db, current_user.id, "EXPORT", "full_database",
                 ip_address=request.client.host if request.client else None)
    return FileResponse(path, filename=os.path.basename(path), media_type="application/zip")
