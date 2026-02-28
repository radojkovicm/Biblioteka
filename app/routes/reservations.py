from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reservation import Reservation
from app.models.book import Book
from app.models.book_copy import BookCopy
from app.models.member import Member
from app.schemas.reservation import ReservationCreate, ReservationOut
from app.utils.auth import get_current_user, check_permission
from app.models.staff import Staff
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=list[ReservationOut])
def list_reservations(
    status: Optional[str] = Query(None),
    current_user: Staff = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Reservation)
    if status:
        query = query.filter(Reservation.status == status)
    reservations = query.order_by(Reservation.reserved_at.desc()).all()

    result = []
    for r in reservations:
        book = db.query(Book).filter(Book.id == r.book_id).first()
        member = db.query(Member).filter(Member.id == r.member_id).first()
        result.append(ReservationOut(
            id=r.id, book_id=r.book_id, member_id=r.member_id,
            reserved_at=r.reserved_at, queue_position=r.queue_position,
            status=r.status, notified_at=r.notified_at, expires_at=r.expires_at,
            book_title=book.title if book else None,
            book_author=book.author if book else None,
            member_name=f"{member.first_name} {member.last_name}" if member else None,
            member_number=member.member_number if member else None,
        ))
    return result


@router.post("", response_model=ReservationOut)
def create_reservation(data: ReservationCreate,
                       current_user: Staff = Depends(check_permission("reservations", write=True)),
                       db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == data.book_id, Book.is_deleted == False).first()
    if not book:
        raise HTTPException(status_code=404, detail="Knjiga nije pronađena")
    member = db.query(Member).filter(Member.id == data.member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen")
    if member.is_blocked:
        raise HTTPException(status_code=400, detail="Član je blokiran")

    # Check if member already has active reservation for this book
    existing = db.query(Reservation).filter(
        Reservation.book_id == data.book_id,
        Reservation.member_id == data.member_id,
        Reservation.status.in_(["waiting", "notified"]),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Član već ima aktivnu rezervaciju za ovu knjigu")

    # Queue position
    last_pos = db.query(Reservation).filter(
        Reservation.book_id == data.book_id,
        Reservation.status == "waiting",
    ).count()

    reservation = Reservation(
        book_id=data.book_id,
        member_id=data.member_id,
        queue_position=last_pos + 1,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    log_activity(db, current_user.id, "CREATE", "reservation", reservation.id,
                 new_values={"book_id": data.book_id, "member_id": data.member_id})

    return ReservationOut(
        id=reservation.id, book_id=reservation.book_id, member_id=reservation.member_id,
        reserved_at=reservation.reserved_at, queue_position=reservation.queue_position,
        status=reservation.status,
        book_title=book.title, book_author=book.author,
        member_name=f"{member.first_name} {member.last_name}",
        member_number=member.member_number,
    )


@router.post("/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int,
                       current_user: Staff = Depends(check_permission("reservations", write=True)),
                       db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervacija nije pronađena")
    if reservation.status in ("fulfilled", "cancelled"):
        raise HTTPException(status_code=400, detail="Rezervacija je već završena")

    was_notified = reservation.status == "notified"
    reservation.status = "cancelled"

    # If copy was reserved for this, make it available
    if was_notified:
        copies = db.query(BookCopy).filter(
            BookCopy.book_id == reservation.book_id,
            BookCopy.status == "reserved",
            BookCopy.is_deleted == False,
        ).all()
        for c in copies:
            c.status = "available"

    db.commit()
    log_activity(db, current_user.id, "UPDATE", "reservation", reservation.id,
                 new_values={"status": "cancelled"})
    return {"message": "Rezervacija otkazana"}


@router.post("/{reservation_id}/fulfill")
def fulfill_reservation(reservation_id: int,
                        current_user: Staff = Depends(check_permission("reservations", write=True)),
                        db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervacija nije pronađena")
    if reservation.status != "notified":
        raise HTTPException(status_code=400, detail="Rezervacija nije u statusu 'notified'")

    reservation.status = "fulfilled"
    db.commit()
    log_activity(db, current_user.id, "UPDATE", "reservation", reservation.id,
                 new_values={"status": "fulfilled"})
    return {"message": "Rezervacija ispunjena"}
