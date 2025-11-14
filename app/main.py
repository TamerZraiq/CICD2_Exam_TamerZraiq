# app/main.py
from typing import Optional

from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Response, Body
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.database import engine, SessionLocal
from app.models import Base, AuthorDB, BookDB
from app.schemas import(
    AuthorCreate, AuthorRead,
    BookCreate, BookRead,
    AuthorReadWithBooks, BookReadWithAuthor
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev/exam). Prefer Alembic in production.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

def commit_or_rollback(db:Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code = 409, detail=error_msg)

# ---- Health ----
@app.get("/health")
def health():
    return {"status": "ok"}

#Authors
@app.get("/api/authors", response_model=list[AuthorRead])
def list_authors(db: Session = Depends(get_db)):
    stmt = select(AuthorDB).order_by(AuthorDB.id)
    return db.execute(stmt).scalars().all()

@app.get("/api/authors/{id}", response_model=AuthorRead)
def list_authors_by_id(id: int, db: Session = Depends(get_db)):
    author=db.get(AuthorDB, id)
    if not author:
        raise HTTPException(status_code=404, detail="Author Not found")
    return author

@app.post("/api/authors", response_model=AuthorRead, status_code=status.HTTP_201_CREATED)
def add_author(payload:AuthorCreate, db:Session = Depends(get_db)):
    author = AuthorDB(**payload.model_dump())
    db.add(author)
    try:
        db.commit()
        db.refresh(author)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate Email")
    return author

@app.put("/api/authors/{id}", response_model=AuthorRead)
def replace_author(id: int, payload: AuthorCreate, db: Session=Depends(get_db)):
    author = db.get(AuthorDB, id)
    if not author:
        raise HTTPException(status_code=404, detail="Author Not found")
    for field, value in payload.model_dump().items():
        setattr(author, field, value)
    commit_or_rollback(db, "Author Update Failed")
    db.refresh(author)
    return author

@app.patch("/api/authors/{id}", response_model=AuthorRead)
def patch_author(id: int, payload: dict=Body(...), db: Session=Depends(get_db)):
    author = db.get(AuthorDB, id)
    if not author:
        raise HTTPException(status_code=404, detail="Author Not found")
    for field, value in payload.items():
        if hasattr(author, field):
            setattr(author, field, value)
    commit_or_rollback(db, "Author Update Failed")
    db.refresh(author)
    return author

@app.delete("/api/authors/{id}", status_code=204)
def delete_author(id:int, db: Session=Depends(get_db)):
    author = db.get(AuthorDB, id)
    if not author:
        raise HTTPException(status_code=404, detail="Author Not found")
    db.delete(author)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

#Books
@app.post("/api/books", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(book:BookCreate, db:Session = Depends(get_db)):
    author = db.get(AuthorDB, book.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Book Not found")
    bk = BookDB(
        title= book.title,
        pages= book.pages,
        author_id= book.author_id,
    )
    db.add(bk)
    commit_or_rollback(db, "Book Creation Failed")
    db.refresh(bk)
    return bk

@app.get("/api/books", response_model=list[BookRead])
def list_books(db: Session = Depends(get_db)):
    stmt = select(BookDB).order_by(BookDB.id)
    return db.execute(stmt).scalars().all()

@app.get("/api/books/{id}", response_model=BookReadWithAuthor)
def list_book_by_id(id: int, db: Session = Depends(get_db)):
    stmt= select(BookDB).where(BookDB.id==id).options(selectinload(BookDB.author))
    bk = db.execute(stmt).scalar_one_or_none()
    if not bk:
        raise HTTPException(status_code=404, detail="Book Not found")
    return bk