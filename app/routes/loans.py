from datetime import datetime, timedelta, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loan import Loan
from app.models.book_copy import BookCopy
from app.models.book import Book
from app.models.member import Member
from app.models.reservation import Reservation
from app.models.setting import Setting
from app.schemas.loan import LoanCreate, LoanOut
from app.utils.auth import get_current_user, check_permission
from app.models.staff import Staff
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/loans", tags=["loans"])


def _get_loan_duration(db: Session) -> int:
    s = db.query(Setting).filter(Setting.key == "loan_duration_days").first()
    return int(s.value) if s else 30


@router.post("", response_model=LoanOut)
def create_loan(data: LoanCreate, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    copy = db.query(BookCopy).filter(BookCopy.id == data.copy_id, BookCopy.is_deleted == False).first()
    if not copy:
        raise HTTPException(status_code=404, detail="Primerak nije pronađen")
    if copy.status != "available":
        raise HTTPException(status_code=400, detail=f"Primerak nije dostupan (status: {copy.status})")

    member = db.query(Member).filter(Member.id == data.member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen")
    if member.is_blocked:
        raise HTTPException(status_code=400, detail="Član je blokiran")
    if not member.is_active:
        raise HTTPException(status_code=400, detail="Član nije aktivan")

    duration = _get_loan_duration(db)
    due = date.today() + timedelta(days=duration)

    loan = Loan(
        copy_id=data.copy_id,
        member_id=data.member_id,
        loaned_at=datetime.utcnow(),
        due_date=due,
        status="active",
        issued_by=current_user.id,
    )
    db.add(loan)
    copy.status = "loaned"
    db.commit()
    db.refresh(loan)

    book = db.query(Book).filter(Book.id == copy.book_id).first()
    log_activity(db, current_user.id, "CREATE", "loan", loan.id,
                 new_values={"member_id": data.member_id, "copy_id": data.copy_id,
                             "book_title": book.title if book else None, "due_date": str(due)},
                 ip_address=request.client.host if request.client else None)

    return LoanOut(
        id=loan.id, copy_id=loan.copy_id, member_id=loan.member_id,
        loaned_at=loan.loaned_at, due_date=loan.due_date,
        returned_at=loan.returned_at, status=loan.status,
        extensions_count=loan.extensions_count, issued_by=loan.issued_by,
        book_title=book.title if book else None,
        book_author=book.author if book else None,
        library_number=copy.library_number,
        member_name=f"{member.first_name} {member.last_name}",
        member_number=member.member_number,
    )


@router.post("/{loan_id}/return")
def return_loan(loan_id: int, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Pozajmica nije pronađena")
    if loan.status == "returned":
        raise HTTPException(status_code=400, detail="Knjiga je već vraćena")

    loan.returned_at = datetime.utcnow()
    loan.status = "returned"
    loan.returned_to = current_user.id

    copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
    if copy:
        # Check if there's a reservation waiting for this book
        reservation = db.query(Reservation).filter(
            Reservation.book_id == copy.book_id,
            Reservation.status == "waiting",
        ).order_by(Reservation.queue_position).first()
        if reservation:
            copy.status = "reserved"
            reservation.status = "notified"
            reservation.notified_at = datetime.utcnow()
            # expires in 7 days
            reservation.expires_at = datetime.utcnow() + timedelta(days=7)
        else:
            copy.status = "available"

    db.commit()
    book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
    log_activity(db, current_user.id, "UPDATE", "loan", loan.id,
                 new_values={"status": "returned", "returned_at": str(loan.returned_at)},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Knjiga vraćena", "reservation_notified": reservation.id if copy and reservation else None}


@router.post("/{loan_id}/extend")
def extend_loan(loan_id: int, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Pozajmica nije pronađena")
    if loan.status != "active":
        raise HTTPException(status_code=400, detail="Pozajmica nije aktivna")
    if loan.extensions_count >= 2:
        raise HTTPException(status_code=400, detail="Maksimalan broj produženja (2)")

    # Check if book is reserved by someone else
    copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
    if copy:
        waiting = db.query(Reservation).filter(
            Reservation.book_id == copy.book_id,
            Reservation.status == "waiting",
        ).count()
        if waiting > 0:
            raise HTTPException(status_code=400, detail="Knjiga je rezervisana — ne može se produžiti")

    duration = _get_loan_duration(db)
    loan.due_date = loan.due_date + timedelta(days=duration)
    loan.extensions_count += 1
    db.commit()

    log_activity(db, current_user.id, "UPDATE", "loan", loan.id,
                 new_values={"due_date": str(loan.due_date), "extensions_count": loan.extensions_count},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Pozajmica produžena", "new_due_date": str(loan.due_date)}


@router.get("/overdue")
def overdue_loans(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    loans = db.query(Loan).filter(
        Loan.status.in_(["active", "overdue"]),
        Loan.due_date < date.today(),
    ).order_by(Loan.due_date).all()

    result = []
    for loan in loans:
        if loan.status == "active":
            loan.status = "overdue"
        copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
        book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
        member = db.query(Member).filter(Member.id == loan.member_id).first()
        days_late = (date.today() - loan.due_date).days
        result.append({
            "id": loan.id,
            "book_title": book.title if book else None,
            "book_author": book.author if book else None,
            "library_number": copy.library_number if copy else None,
            "member_name": f"{member.first_name} {member.last_name}" if member else None,
            "member_number": member.member_number if member else None,
            "member_email": member.email if member else None,
            "due_date": str(loan.due_date),
            "days_late": days_late,
        })
    db.commit()
    return result


@router.get("/active")
def active_loans(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: Staff = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Loan).filter(Loan.status.in_(["active", "overdue"])).order_by(Loan.due_date)
    loans = query.offset((page - 1) * per_page).limit(per_page).all()
    result = []
    for loan in loans:
        copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
        book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
        member = db.query(Member).filter(Member.id == loan.member_id).first()
        result.append({
            "id": loan.id,
            "copy_id": loan.copy_id,
            "member_id": loan.member_id,
            "loaned_at": loan.loaned_at,
            "due_date": str(loan.due_date),
            "status": loan.status,
            "extensions_count": loan.extensions_count,
            "book_title": book.title if book else None,
            "book_author": book.author if book else None,
            "library_number": copy.library_number if copy else None,
            "member_name": f"{member.first_name} {member.last_name}" if member else None,
            "member_number": member.member_number if member else None,
        })
    return result
