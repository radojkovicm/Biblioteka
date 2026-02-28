from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models.book import Book
from app.models.book_copy import BookCopy
from app.schemas.book import (
    BookCreate, BookUpdate, BookOut, BookDetailOut,
    BookCopyCreate, BookCopyUpdate, BookCopyOut,
)
from app.utils.auth import get_current_user, check_permission
from app.models.staff import Staff
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/books", tags=["books"])


def _update_total_copies(db: Session, book_id: int):
    count = db.query(BookCopy).filter(
        BookCopy.book_id == book_id, BookCopy.is_deleted == False
    ).count()
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        book.total_copies = count
        db.commit()


@router.get("", response_model=list[BookOut])
def list_books(
    q: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: Staff = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Book).filter(Book.is_deleted == False)
    if q:
        search = f"%{q}%"
        query = query.filter(or_(
            Book.title.ilike(search),
            Book.author.ilike(search),
        ))
    if genre:
        query = query.filter(Book.genre == genre)
    query = query.order_by(Book.title)
    total = query.count()
    books = query.offset((page - 1) * per_page).limit(per_page).all()

    # Compute available copies for each book
    book_ids = [b.id for b in books]
    if book_ids:
        avail_counts = dict(
            db.query(BookCopy.book_id, func.count(BookCopy.id))
            .filter(
                BookCopy.book_id.in_(book_ids),
                BookCopy.status == "available",
                BookCopy.is_deleted == False,
            )
            .group_by(BookCopy.book_id)
            .all()
        )
    else:
        avail_counts = {}

    result = []
    for b in books:
        out = BookOut.model_validate(b)
        out.available_copies = avail_counts.get(b.id, 0)
        result.append(out)
    return result


@router.get("/genres")
def list_genres(current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Book.genre).filter(Book.is_deleted == False, Book.genre.isnot(None)).distinct().all()
    return [r[0] for r in rows if r[0]]


@router.get("/{book_id}", response_model=BookDetailOut)
def get_book(book_id: int, current_user: Staff = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id, Book.is_deleted == False).first()
    if not book:
        raise HTTPException(status_code=404, detail="Knjiga nije pronađena")
    copies = db.query(BookCopy).filter(BookCopy.book_id == book_id, BookCopy.is_deleted == False).all()
    return BookDetailOut(
        id=book.id, title=book.title, author=book.author, publisher=book.publisher,
        year_published=book.year_published, genre=book.genre, language=book.language,
        description=book.description, total_copies=book.total_copies, copies=copies,
    )


@router.post("", response_model=BookOut)
def create_book(data: BookCreate, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    book = Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    log_activity(db, current_user.id, "CREATE", "book", book.id,
                 new_values=data.model_dump(),
                 ip_address=request.client.host if request.client else None)
    return book


@router.put("/{book_id}", response_model=BookOut)
def update_book(book_id: int, data: BookUpdate, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id, Book.is_deleted == False).first()
    if not book:
        raise HTTPException(status_code=404, detail="Knjiga nije pronađena")
    old_values = {"title": book.title, "author": book.author}
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    log_activity(db, current_user.id, "UPDATE", "book", book.id,
                 old_values=old_values,
                 new_values=data.model_dump(exclude_unset=True),
                 ip_address=request.client.host if request.client else None)
    return book


@router.delete("/{book_id}")
def delete_book(book_id: int, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id, Book.is_deleted == False).first()
    if not book:
        raise HTTPException(status_code=404, detail="Knjiga nije pronađena")
    book.is_deleted = True
    book.deleted_at = datetime.utcnow()
    book.deleted_by = current_user.id
    db.commit()
    log_activity(db, current_user.id, "DELETE", "book", book.id,
                 old_values={"title": book.title},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Knjiga obrisana"}


# --- Book Copies ---

@router.post("/{book_id}/copies", response_model=BookCopyOut)
def add_copy(book_id: int, data: BookCopyCreate, request: Request,
             current_user: Staff = Depends(check_permission("books", write=True)),
             db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id, Book.is_deleted == False).first()
    if not book:
        raise HTTPException(status_code=404, detail="Knjiga nije pronađena")
    if db.query(BookCopy).filter(BookCopy.library_number == data.library_number).first():
        raise HTTPException(status_code=400, detail="Broj primerka već postoji")
    copy = BookCopy(book_id=book_id, **data.model_dump())
    db.add(copy)
    db.commit()
    _update_total_copies(db, book_id)
    db.refresh(copy)
    log_activity(db, current_user.id, "CREATE", "book_copy", copy.id,
                 new_values={"library_number": copy.library_number, "book_id": book_id},
                 ip_address=request.client.host if request.client else None)
    return copy


@router.put("/copies/{copy_id}", response_model=BookCopyOut)
def update_copy(copy_id: int, data: BookCopyUpdate, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    copy = db.query(BookCopy).filter(BookCopy.id == copy_id, BookCopy.is_deleted == False).first()
    if not copy:
        raise HTTPException(status_code=404, detail="Primerak nije pronađen")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(copy, field, value)
    db.commit()
    db.refresh(copy)
    return copy


@router.delete("/copies/{copy_id}")
def delete_copy(copy_id: int, request: Request,
                current_user: Staff = Depends(check_permission("books", write=True)),
                db: Session = Depends(get_db)):
    copy = db.query(BookCopy).filter(BookCopy.id == copy_id, BookCopy.is_deleted == False).first()
    if not copy:
        raise HTTPException(status_code=404, detail="Primerak nije pronađen")
    copy.is_deleted = True
    copy.deleted_at = datetime.utcnow()
    copy.deleted_by = current_user.id
    db.commit()
    _update_total_copies(db, copy.book_id)
    log_activity(db, current_user.id, "DELETE", "book_copy", copy.id,
                 old_values={"library_number": copy.library_number},
                 ip_address=request.client.host if request.client else None)
    return {"message": "Primerak otpisan"}


@router.get("/copy/{library_number}", response_model=BookCopyOut)
def get_copy_by_number(library_number: str, current_user: Staff = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    copy = db.query(BookCopy).filter(
        BookCopy.library_number == library_number, BookCopy.is_deleted == False
    ).first()
    if not copy:
        raise HTTPException(status_code=404, detail="Primerak nije pronađen")
    return copy


@router.get("/{book_id}/availability")
def book_availability(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id, Book.is_deleted == False).first()
    if not book:
        raise HTTPException(status_code=404, detail="Knjiga nije pronađena")
    available = db.query(BookCopy).filter(
        BookCopy.book_id == book_id, BookCopy.status == "available", BookCopy.is_deleted == False
    ).count()
    total = db.query(BookCopy).filter(
        BookCopy.book_id == book_id, BookCopy.is_deleted == False
    ).count()
    return {"book_id": book_id, "title": book.title, "available": available, "total": total}
