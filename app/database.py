import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_PATH = os.environ.get("DATABASE_PATH", "library.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import (
        Member, Membership, Book, BookCopy, Loan,
        Reservation, Staff, ActivityLog, Setting,
        UserPermission, Notification,
    )
    Base.metadata.create_all(bind=engine)
    _create_indices()
    _seed_defaults()


def _create_indices():
    from sqlalchemy import text
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)",
        "CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)",
        "CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre)",
        "CREATE INDEX IF NOT EXISTS idx_copies_lib_number ON book_copies(library_number)",
        "CREATE INDEX IF NOT EXISTS idx_copies_status ON book_copies(status)",
        "CREATE INDEX IF NOT EXISTS idx_members_last_name ON members(last_name)",
        "CREATE INDEX IF NOT EXISTS idx_members_number ON members(member_number)",
        "CREATE INDEX IF NOT EXISTS idx_loans_member ON loans(member_id)",
        "CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status)",
        "CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_entity ON activity_log(entity, entity_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_trigger ON notifications(trigger_type, entity_id)",
    ]
    with engine.connect() as conn:
        for idx in indices:
            conn.execute(text(idx))
        conn.commit()


def _seed_defaults():
    from app.models.staff import Staff
    from app.models.setting import Setting
    from passlib.hash import bcrypt

    db = SessionLocal()
    try:
        if db.query(Staff).count() == 0:
            admin = Staff(
                username="admin",
                full_name="Administrator",
                password_hash=bcrypt.hash("admin123"),
                is_admin=True,
                is_active=True,
            )
            db.add(admin)

        default_settings = {
            "library_name": "Biblioteka",
            "library_logo_path": "",
            "loan_duration_days": "30",
            "membership_prices": '{"djak": 500, "student": 700, "odrasli": 1000, "penzioner": 600, "institucija": 2000}',
            "email_smtp_host": "",
            "email_smtp_port": "587",
            "email_smtp_user": "",
            "email_smtp_password": "",
            "email_sender_name": "Biblioteka",
            "email_enabled": "false",
            "currency": "RSD",
            "language": "sr",
        }
        for key, value in default_settings.items():
            if not db.query(Setting).filter_by(key=key).first():
                db.add(Setting(key=key, value=value))

        db.commit()
    finally:
        db.close()
