import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base

# Shared in-memory DB across all sessions/connections in this process
TEST_DB_URL = "sqlite+pysqlite://"

engine = create_engine(
    TEST_DB_URL,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,      # <- keeps the same in-memory DB for every connection
)

@event.listens_for(engine, "connect")
def _fk_pragma_on_connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

# Create tables on the TEST engine (not the app's file DB)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
            db.commit()
        except:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
