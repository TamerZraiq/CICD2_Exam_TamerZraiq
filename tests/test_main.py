import pytest
from fastapi.testclient import TestClient 
from app.main import app, get_db
from app.models import Base, BookDB, AuthorDB
from app.database import engine, SessionLocal
import uuid

#Database Setup
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = SessionLocal

#Fixtures
@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    
@pytest.fixture
def test_author(db):
    email = f"alice_{uuid.uuid4().hex[:6]}@example.com"
    author = AuthorDB(name = "Alice", email = email, year_started = 2000)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author

@pytest.fixture
def test_book(db, test_author):
    book = BookDB(title = "Book1", pages = 100, author_id = test_author.id)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

#tests
def test_create_author(client):
    unique = str(uuid.uuid4())
    r = client.post(
        "/api/authors",
        json = {"name": "Tamer", "email":f"tz_{unique}@atu.ie", "year_started":2001},
    )
    assert r.status_code==201, r.text
    assert r.json()["name"] == "Tamer"

def test_get_authors(client):
    r = client.get(
        "/api/authors"
    )
    assert r.status_code==200, r.text

def test_put_author(client, test_author):
    unique = str(uuid.uuid4().hex[:6])
    data = {"name": "Updated", "email":f"new_{unique}@example.com", "year_started":2010}
    res = client.put(f"/api/authors/{id}", json = data)
    assert res.status_code==422, res.text
    assert res.json()["name"] == "Updated"

def test_patch_author(client, test_author):
    new_email = f"patched_{uuid.uuid4().hex[:6]}@example.com"
    data = {"email": new_email}
    res = client.put(f"/api/authors/{id}", json = data)
    assert res.status_code==422, res.text
    assert res.json()["email"] == new_email

def test_create_book(client, test_author):
    r = client.post(
        "/api/books",
        json = {"title": "Book2", "pages":200, "author_id": test_author.id},
    )
    assert r.status_code==201, r.text
    assert r.json()["title"] == "Book2"

def test_get_books(client):
    r = client.get(
        "/api/books"
    )
    assert r.status_code==200, r.text

def test_put_book(client, test_book, test_author):
    data = {"title": "Replaced Book", "pages" : 10, "author_id": test_author.id}
    res = client.put(f"/api/books/{id}", json = data)
    assert res.status_code==405, res.text
    assert res.json()["title"] == "Replaced Book"

def test_patch_book(client, test_book):
    data = {"pages" : 12}
    res = client.put(f"/api/books/{id}", json = data)
    assert res.status_code==405, res.text
    assert res.json()["pages"] == 12

