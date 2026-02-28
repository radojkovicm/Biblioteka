import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from app.models.setting import Setting
from app.models.loan import Loan
from app.models.book_copy import BookCopy
from app.models.book import Book
from app.models.member import Member
from app.models.membership import Membership
from app.models.reservation import Reservation
from app.models.notification import Notification


def get_email_config(db: Session) -> dict:
    settings = {}
    for s in db.query(Setting).filter(Setting.key.like("email_%")).all():
        settings[s.key] = s.value
    return {
        "host": settings.get("email_smtp_host", ""),
        "port": int(settings.get("email_smtp_port", "587")),
        "user": settings.get("email_smtp_user", ""),
        "password": settings.get("email_smtp_password", ""),
        "sender_name": settings.get("email_sender_name", "Biblioteka"),
        "enabled": settings.get("email_enabled", "false").lower() == "true",
    }


def send_email(config: dict, to_email: str, subject: str, body: str) -> Tuple[bool, Optional[str]]:
    if not config["enabled"] or not config["host"] or not config["user"]:
        return False, "Email nije konfigurisan"

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{config['sender_name']} <{config['user']}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP(config["host"], config["port"], timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(config["user"], config["password"])
            server.sendmail(config["user"], to_email, msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


def _already_sent(db: Session, trigger_type: str, entity_id: int) -> bool:
    """Check if notification was already sent for this trigger+entity combo."""
    existing = db.query(Notification).filter(
        Notification.trigger_type == trigger_type,
        Notification.entity_id == entity_id,
        Notification.success == True,
    ).first()
    return existing is not None


def _already_sent_this_week(db: Session, trigger_type: str, entity_id: int) -> bool:
    """For weekly triggers — check if sent in last 7 days."""
    week_ago = datetime.utcnow() - timedelta(days=7)
    existing = db.query(Notification).filter(
        Notification.trigger_type == trigger_type,
        Notification.entity_id == entity_id,
        Notification.success == True,
        Notification.sent_at >= week_ago,
    ).first()
    return existing is not None


def _record_notification(db: Session, trigger_type: str, entity_id: int,
                         member_id: int, email: str, subject: str, body: str,
                         success: bool, error: str = None):
    notif = Notification(
        trigger_type=trigger_type,
        entity_id=entity_id,
        member_id=member_id,
        email_to=email,
        subject=subject,
        body=body,
        success=success,
        error_message=error,
    )
    db.add(notif)
    db.commit()


def _get_library_name(db: Session) -> str:
    s = db.query(Setting).filter(Setting.key == "library_name").first()
    return s.value if s else "Biblioteka"


def process_due_tomorrow(db: Session, config: dict):
    """Rok vraćanja — sutra. Šalje se svako veče."""
    tomorrow = date.today() + timedelta(days=1)
    loans = db.query(Loan).filter(
        Loan.status == "active",
        Loan.due_date == tomorrow,
    ).all()

    library_name = _get_library_name(db)

    for loan in loans:
        if _already_sent(db, "due_tomorrow", loan.id):
            continue
        member = db.query(Member).filter(Member.id == loan.member_id).first()
        if not member or not member.email:
            continue
        copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
        book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
        book_title = book.title if book else "Nepoznata knjiga"

        subject = f"Podsetnik: knjiga \"{book_title}\" se vraća sutra"
        body = (
            f"Poštovani/a {member.first_name} {member.last_name},\n\n"
            f"Podsetnik da knjiga \"{book_title}\" treba da se vrati sutra ({tomorrow.strftime('%d.%m.%Y.')}).\n\n"
            f"Molimo vas da knjigu vratite na vreme.\n\n"
            f"Srdačan pozdrav,\n{library_name}"
        )

        success, error = send_email(config, member.email, subject, body)
        _record_notification(db, "due_tomorrow", loan.id, member.id, member.email, subject, body, success, error)


def process_due_today(db: Session, config: dict):
    """Rok vraćanja — danas. Šalje se ujutro na dan roka."""
    today = date.today()
    loans = db.query(Loan).filter(
        Loan.status == "active",
        Loan.due_date == today,
    ).all()

    library_name = _get_library_name(db)

    for loan in loans:
        if _already_sent(db, "due_today", loan.id):
            continue
        member = db.query(Member).filter(Member.id == loan.member_id).first()
        if not member or not member.email:
            continue
        copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
        book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
        book_title = book.title if book else "Nepoznata knjiga"

        subject = f"Danas je rok za vraćanje knjige \"{book_title}\""
        body = (
            f"Poštovani/a {member.first_name} {member.last_name},\n\n"
            f"Danas ({today.strftime('%d.%m.%Y.')}) ističe rok za vraćanje knjige \"{book_title}\".\n\n"
            f"Molimo vas da knjigu vratite danas.\n\n"
            f"Srdačan pozdrav,\n{library_name}"
        )

        success, error = send_email(config, member.email, subject, body)
        _record_notification(db, "due_today", loan.id, member.id, member.email, subject, body, success, error)


def process_overdue(db: Session, config: dict):
    """Knjiga kasni. Jednom nedeljno podsetnik."""
    today = date.today()
    loans = db.query(Loan).filter(
        Loan.status.in_(["active", "overdue"]),
        Loan.due_date < today,
    ).all()

    library_name = _get_library_name(db)

    for loan in loans:
        if _already_sent_this_week(db, "overdue_weekly", loan.id):
            continue
        member = db.query(Member).filter(Member.id == loan.member_id).first()
        if not member or not member.email:
            continue
        copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
        book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
        book_title = book.title if book else "Nepoznata knjiga"
        days_late = (today - loan.due_date).days

        subject = f"Knjiga \"{book_title}\" kasni {days_late} dana"
        body = (
            f"Poštovani/a {member.first_name} {member.last_name},\n\n"
            f"Knjiga \"{book_title}\" je trebalo da bude vraćena {loan.due_date.strftime('%d.%m.%Y.')}.\n"
            f"Kasni već {days_late} dana.\n\n"
            f"Molimo vas da knjigu vratite što pre.\n\n"
            f"Srdačan pozdrav,\n{library_name}"
        )

        success, error = send_email(config, member.email, subject, body)
        _record_notification(db, "overdue_weekly", loan.id, member.id, member.email, subject, body, success, error)


def process_reservation_available(db: Session, config: dict):
    """Rezervacija dostupna — odmah kad se vrati knjiga.
    This is triggered from the return_loan endpoint. Here we check for any
    notified reservations that haven't had an email sent yet."""
    reservations = db.query(Reservation).filter(
        Reservation.status == "notified",
    ).all()

    library_name = _get_library_name(db)

    for reservation in reservations:
        if _already_sent(db, "reservation_available", reservation.id):
            continue
        member = db.query(Member).filter(Member.id == reservation.member_id).first()
        if not member or not member.email:
            continue
        book = db.query(Book).filter(Book.id == reservation.book_id).first()
        book_title = book.title if book else "Nepoznata knjiga"

        expires_str = ""
        if reservation.expires_at:
            expires_str = f"\nKnjigu možete preuzeti do {reservation.expires_at.strftime('%d.%m.%Y.')}."

        subject = f"Vaša rezervacija je dostupna: \"{book_title}\""
        body = (
            f"Poštovani/a {member.first_name} {member.last_name},\n\n"
            f"Knjiga \"{book_title}\" koju ste rezervisali je sada dostupna za preuzimanje.{expires_str}\n\n"
            f"Srdačan pozdrav,\n{library_name}"
        )

        success, error = send_email(config, member.email, subject, body)
        _record_notification(db, "reservation_available", reservation.id, member.id, member.email, subject, body, success, error)


def process_membership_expiring(db: Session, config: dict):
    """Članarina ističe za 30 dana."""
    target_date = date.today() + timedelta(days=30)
    memberships = db.query(Membership).filter(
        Membership.valid_until == target_date,
    ).all()

    library_name = _get_library_name(db)

    for membership in memberships:
        if _already_sent(db, "membership_expiring", membership.id):
            continue
        member = db.query(Member).filter(Member.id == membership.member_id).first()
        if not member or not member.email:
            continue

        subject = "Članarina ističe za 30 dana"
        body = (
            f"Poštovani/a {member.first_name} {member.last_name},\n\n"
            f"Vaša članarina u biblioteci ističe {membership.valid_until.strftime('%d.%m.%Y.')}.\n\n"
            f"Molimo vas da obnovite članarinu na vreme.\n\n"
            f"Srdačan pozdrav,\n{library_name}"
        )

        success, error = send_email(config, member.email, subject, body)
        _record_notification(db, "membership_expiring", membership.id, member.id, member.email, subject, body, success, error)


def process_membership_expired(db: Session, config: dict):
    """Članarina istekla — na dan isteka."""
    today = date.today()
    memberships = db.query(Membership).filter(
        Membership.valid_until == today,
    ).all()

    library_name = _get_library_name(db)

    for membership in memberships:
        if _already_sent(db, "membership_expired", membership.id):
            continue
        member = db.query(Member).filter(Member.id == membership.member_id).first()
        if not member or not member.email:
            continue

        subject = "Vaša članarina je istekla"
        body = (
            f"Poštovani/a {member.first_name} {member.last_name},\n\n"
            f"Vaša članarina u biblioteci je istekla danas ({today.strftime('%d.%m.%Y.')}).\n\n"
            f"Molimo vas da obnovite članarinu kako biste nastavili da koristite usluge biblioteke.\n\n"
            f"Srdačan pozdrav,\n{library_name}"
        )

        success, error = send_email(config, member.email, subject, body)
        _record_notification(db, "membership_expired", membership.id, member.id, member.email, subject, body, success, error)


def run_all_notifications(db: Session):
    """Run all notification checks. Called by scheduler."""
    config = get_email_config(db)
    if not config["enabled"]:
        return

    process_due_tomorrow(db, config)
    process_due_today(db, config)
    process_overdue(db, config)
    process_reservation_available(db, config)
    process_membership_expiring(db, config)
    process_membership_expired(db, config)
