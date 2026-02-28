import os
import shutil
import zipfile
from datetime import datetime, timedelta
from app.database import DATABASE_PATH

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backups")


def _ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def auto_backup():
    """Daily auto backup — keeps last 7 days."""
    _ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    dest = os.path.join(BACKUP_DIR, f"library_{timestamp}.db")

    if not os.path.exists(DATABASE_PATH):
        return None

    shutil.copy2(DATABASE_PATH, dest)

    # Clean old backups (older than 7 days)
    cutoff = datetime.now() - timedelta(days=7)
    for f in os.listdir(BACKUP_DIR):
        if f.startswith("library_") and f.endswith(".db"):
            try:
                date_str = f.replace("library_", "").replace(".db", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    os.remove(os.path.join(BACKUP_DIR, f))
            except ValueError:
                pass

    return dest


def manual_backup() -> str:
    """Manual backup — triggered by admin button."""
    _ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"library_manual_{timestamp}.db")

    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError("Baza podataka nije pronađena")

    shutil.copy2(DATABASE_PATH, dest)
    return dest


def export_full_database() -> str:
    """Export complete database as ZIP with .db and Excel files."""
    from app.services.excel import export_books_to_excel, export_members_to_excel

    _ensure_backup_dir()
    export_dir = os.path.join(os.path.dirname(BACKUP_DIR), "exports")
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    zip_path = os.path.join(export_dir, f"biblioteka_export_{timestamp}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add database file
        if os.path.exists(DATABASE_PATH):
            zf.write(DATABASE_PATH, "library.db")

        # Add Excel exports
        books_path = export_books_to_excel()
        if books_path and os.path.exists(books_path):
            zf.write(books_path, "knjige.xlsx")
            os.remove(books_path)

        members_path = export_members_to_excel()
        if members_path and os.path.exists(members_path):
            zf.write(members_path, "clanovi.xlsx")
            os.remove(members_path)

    return zip_path


def list_backups() -> list:
    """List all backups."""
    _ensure_backup_dir()
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(".db"):
            fpath = os.path.join(BACKUP_DIR, f)
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            backups.append({
                "filename": f,
                "size_mb": round(size_mb, 2),
                "created_at": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
            })
    return backups
