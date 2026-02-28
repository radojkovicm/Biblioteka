from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.loan import Loan
from app.models.book_copy import BookCopy
from app.models.book import Book
from app.models.member import Member
from app.models.membership import Membership
from app.models.reservation import Reservation
from app.models.activity_log import ActivityLog
from app.models.staff import Staff
from app.utils.auth import get_current_user, check_permission

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
def dashboard(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    active_loans = db.query(Loan).filter(Loan.status.in_(["active", "overdue"])).count()
    overdue_loans = db.query(Loan).filter(Loan.status == "overdue").count()

    # Expired memberships: members whose latest membership valid_until < today
    today = date.today()
    from sqlalchemy import and_
    # Members with no valid membership for this year
    members_total = db.query(Member).filter(Member.is_deleted == False, Member.is_active == True).count()
    members_with_valid = db.query(Membership.member_id).filter(
        Membership.valid_until >= today
    ).distinct().count()
    expired_memberships = members_total - members_with_valid

    waiting_reservations = db.query(Reservation).filter(Reservation.status == "waiting").count()
    total_books = db.query(Book).filter(Book.is_deleted == False).count()
    total_copies = db.query(BookCopy).filter(BookCopy.is_deleted == False).count()

    return {
        "active_loans": active_loans,
        "overdue_loans": overdue_loans,
        "expired_memberships": expired_memberships,
        "waiting_reservations": waiting_reservations,
        "total_books": total_books,
        "total_copies": total_copies,
        "total_members": members_total,
    }


@router.get("/activity")
def recent_activity(
    limit: int = Query(50, ge=1, le=200),
    current_user: Staff = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    result = []
    for log in logs:
        staff = db.query(Staff).filter(Staff.id == log.user_id).first()
        result.append({
            "id": log.id,
            "user": staff.full_name if staff else "Sistem",
            "action": log.action,
            "entity": log.entity,
            "entity_id": log.entity_id,
            "new_values": log.new_values,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return result


@router.get("/overdue")
def overdue_report(current_user: Staff = Depends(check_permission("reports")),
                   db: Session = Depends(get_db)):
    loans = db.query(Loan).filter(
        Loan.status.in_(["active", "overdue"]),
        Loan.due_date < date.today(),
    ).order_by(Loan.due_date).all()

    result = []
    for loan in loans:
        copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
        book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
        member = db.query(Member).filter(Member.id == loan.member_id).first()
        result.append({
            "loan_id": loan.id,
            "book_title": book.title if book else None,
            "library_number": copy.library_number if copy else None,
            "member_name": f"{member.first_name} {member.last_name}" if member else None,
            "member_number": member.member_number if member else None,
            "member_email": member.email if member else None,
            "member_phone": member.phone if member else None,
            "due_date": str(loan.due_date),
            "days_late": (date.today() - loan.due_date).days,
        })
    return result


@router.get("/memberships")
def membership_report(
    year: Optional[int] = Query(None),
    current_user: Staff = Depends(check_permission("reports")),
    db: Session = Depends(get_db),
):
    query = db.query(Membership)
    if year:
        query = query.filter(Membership.year == year)
    memberships = query.order_by(Membership.paid_at.desc()).all()

    result = []
    total_amount = 0
    for m in memberships:
        member = db.query(Member).filter(Member.id == m.member_id).first()
        total_amount += m.amount_paid
        result.append({
            "membership_id": m.id,
            "member_name": f"{member.first_name} {member.last_name}" if member else None,
            "member_number": member.member_number if member else None,
            "member_type": member.member_type if member else None,
            "year": m.year,
            "amount_paid": m.amount_paid,
            "paid_at": str(m.paid_at),
            "valid_until": str(m.valid_until),
        })
    return {"memberships": result, "total_amount": total_amount, "count": len(result)}


@router.get("/popular-books")
def popular_books(
    limit: int = Query(20, ge=1, le=100),
    current_user: Staff = Depends(check_permission("reports")),
    db: Session = Depends(get_db),
):
    results = (
        db.query(
            Book.id, Book.title, Book.author,
            func.count(Loan.id).label("loan_count"),
        )
        .join(BookCopy, BookCopy.book_id == Book.id)
        .join(Loan, Loan.copy_id == BookCopy.id)
        .filter(Book.is_deleted == False)
        .group_by(Book.id)
        .order_by(func.count(Loan.id).desc())
        .limit(limit)
        .all()
    )
    return [{"id": r[0], "title": r[1], "author": r[2], "loan_count": r[3]} for r in results]


@router.get("/expired-memberships")
def expired_memberships_report(
    current_user: Staff = Depends(check_permission("reports")),
    db: Session = Depends(get_db),
):
    today = date.today()
    members = db.query(Member).filter(Member.is_deleted == False, Member.is_active == True).all()
    result = []
    for member in members:
        latest = db.query(Membership).filter(
            Membership.member_id == member.id
        ).order_by(Membership.valid_until.desc()).first()
        if not latest or latest.valid_until < today:
            result.append({
                "member_id": member.id,
                "member_name": f"{member.first_name} {member.last_name}",
                "member_number": member.member_number,
                "member_type": member.member_type,
                "email": member.email,
                "phone": member.phone,
                "last_valid_until": str(latest.valid_until) if latest else "Nikad",
            })
    return result
