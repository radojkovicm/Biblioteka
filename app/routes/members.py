from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.member import Member
from app.models.membership import Membership
from app.models.loan import Loan
from app.models.book_copy import BookCopy
from app.models.book import Book
from app.schemas.member import (
    MemberCreate, MemberUpdate, MemberOut,
    MemberBlockRequest, MembershipCreate, MembershipOut,
)
from app.schemas.loan import LoanOut
from app.utils.auth import get_current_user, check_permission
from app.models.staff import Staff
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/members", tags=["members"])


def _generate_member_number(db: Session) -> str:
    last = db.query(Member).order_by(Member.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"MBR-{next_num:05d}"


@router.get("", response_model=list[MemberOut])
def list_members(
    q: Optional[str] = Query(None),
    member_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: Staff = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Member).filter(Member.is_deleted == False)
    if active_only:
        query = query.filter(Member.is_active == True)
    if q:
        search = f"%{q}%"
        query = query.filter(or_(
            Member.first_name.ilike(search),
            Member.last_name.ilike(search),
            Member.member_number.ilike(search),
            Member.email.ilike(search),
            Member.phone.ilike(search),
        ))
    if member_type:
        query = query.filter(Member.member_type == member_type)
    query = query.order_by(Member.last_name, Member.first_name)
    members = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Add last_membership to each member
    result = []
    for member in members:
        member_dict = {
            'id': member.id,
            'member_number': member.member_number,
            'first_name': member.first_name,
            'last_name': member.last_name,
            'date_of_birth': member.date_of_birth,
            'email': member.email,
            'phone': member.phone,
            'address': member.address,
            'member_type': member.member_type,
            'is_active': member.is_active,
            'is_blocked': member.is_blocked,
            'block_reason': member.block_reason,
            'allow_notifications': member.allow_notifications,
            'notes': member.notes,
            'registered_at': member.registered_at,
            'last_membership': None
        }
        if member.memberships:
            last_ms = sorted(member.memberships, key=lambda m: m.valid_until, reverse=True)[0]
            member_dict['last_membership'] = {
                'id': last_ms.id,
                'member_id': last_ms.member_id,
                'year': last_ms.year,
                'amount_paid': last_ms.amount_paid,
                'paid_at': last_ms.paid_at,
                'valid_from': last_ms.valid_from,
                'valid_until': last_ms.valid_until,
                'recorded_by': last_ms.recorded_by,
            }
        result.append(member_dict)

    return result


@router.get("/{member_id}", response_model=MemberOut)
def get_member(member_id: int, current_user: Staff = Depends(get_current_user),
               db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen")
    
    # Add last_membership
    member_dict = {
        'id': member.id,
        'member_number': member.member_number,
        'first_name': member.first_name,
        'last_name': member.last_name,
        'date_of_birth': member.date_of_birth,
        'email': member.email,
        'phone': member.phone,
        'address': member.address,
        'member_type': member.member_type,
        'is_active': member.is_active,
        'is_blocked': member.is_blocked,
        'block_reason': member.block_reason,
        'allow_notifications': member.allow_notifications,
        'notes': member.notes,
        'registered_at': member.registered_at,
        'last_membership': None
    }
    if member.memberships:
        last_ms = sorted(member.memberships, key=lambda m: m.valid_until, reverse=True)[0]
        member_dict['last_membership'] = {
            'id': last_ms.id,
            'member_id': last_ms.member_id,
            'year': last_ms.year,
            'amount_paid': last_ms.amount_paid,
            'paid_at': last_ms.paid_at,
            'valid_from': last_ms.valid_from,
            'valid_until': last_ms.valid_until,
            'recorded_by': last_ms.recorded_by,
        }
    return member_dict


@router.post("", response_model=MemberOut)
def create_member(data: MemberCreate, request: Request,
                  current_user: Staff = Depends(check_permission("members", write=True)),
                  db: Session = Depends(get_db)):
    member = Member(
        member_number=str(data.member_number),
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        email=data.email,
        phone=data.phone,
        address=data.address,
        member_type=data.member_type,
        allow_notifications=data.allow_notifications,
        notes=data.notes,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    log_activity(db, current_user.id, "CREATE", "member", member.id,
                 new_values={"member_number": member.member_number, "name": f"{member.first_name} {member.last_name}"},
                 ip_address=request.client.host if request.client else None)
    return member


@router.put("/{member_id}", response_model=MemberOut)
def update_member(member_id: int, data: MemberUpdate, request: Request,
                  current_user: Staff = Depends(check_permission("members", write=True)),
                  db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen")
    old_values = {"first_name": member.first_name, "last_name": member.last_name}
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    log_activity(db, current_user.id, "UPDATE", "member", member.id,
                 old_values=old_values,
                 new_values=data.model_dump(exclude_unset=True),
                 ip_address=request.client.host if request.client else None)
    return member


@router.delete("/{member_id}")
def delete_member(member_id: int, request: Request,
                  current_user: Staff = Depends(check_permission("members", write=True)),
                  db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen")
    member.is_deleted = True
    member.deleted_at = datetime.utcnow()
    member.deleted_by = current_user.id
    db.commit()
    log_activity(db, current_user.id, "DELETE", "member", member.id,
                 old_values={"name": f"{member.first_name} {member.last_name}"},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Član obrisan"}


@router.post("/{member_id}/block")
def block_member(member_id: int, data: MemberBlockRequest, request: Request,
                 current_user: Staff = Depends(check_permission("members", write=True)),
                 db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen")
    member.is_blocked = data.is_blocked
    member.block_reason = data.block_reason if data.is_blocked else None
    db.commit()
    action = "BLOCK" if data.is_blocked else "UNBLOCK"
    log_activity(db, current_user.id, "UPDATE", "member", member.id,
                 new_values={"blocked": data.is_blocked, "reason": data.block_reason},
                 ip_address=request.client.host if request.client else None)
    return {"message": f"Član {'blokiran' if data.is_blocked else 'deblokiran'}"}


# --- Memberships ---

@router.get("/{member_id}/memberships", response_model=list[MembershipOut])
def list_memberships(member_id: int, current_user: Staff = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return db.query(Membership).filter(Membership.member_id == member_id).order_by(Membership.year.desc()).all()


@router.post("/{member_id}/membership", response_model=MembershipOut)
def add_membership(member_id: int, data: MembershipCreate, request: Request,
                   current_user: Staff = Depends(check_permission("members", write=True)),
                   db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen")
    membership = Membership(
        member_id=member_id,
        recorded_by=current_user.id,
        **data.model_dump(),
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    log_activity(db, current_user.id, "CREATE", "membership", membership.id,
                 new_values={"member_id": member_id, "year": data.year, "amount": data.amount_paid},
                 ip_address=request.client.host if request.client else None)
    return membership


# --- Member loans ---

@router.get("/{member_id}/loans")
def member_loans(member_id: int, status: Optional[str] = Query(None),
                 current_user: Staff = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    query = db.query(Loan).filter(Loan.member_id == member_id)
    if status:
        query = query.filter(Loan.status == status)
    loans = query.order_by(Loan.loaned_at.desc()).all()
    result = []
    for loan in loans:
        copy = db.query(BookCopy).filter(BookCopy.id == loan.copy_id).first()
        book = db.query(Book).filter(Book.id == copy.book_id).first() if copy else None
        result.append({
            "id": loan.id,
            "copy_id": loan.copy_id,
            "member_id": loan.member_id,
            "loaned_at": loan.loaned_at,
            "due_date": loan.due_date,
            "returned_at": loan.returned_at,
            "status": loan.status,
            "extensions_count": loan.extensions_count,
            "book_title": book.title if book else None,
            "book_author": book.author if book else None,
            "library_number": copy.library_number if copy else None,
        })
    return result
