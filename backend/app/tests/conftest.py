"""
Test fixtures and configurations
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import uuid

from app.config.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.utils.encryption import hash_password

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Create test SessionLocal
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    """Create a test instance of the FastAPI application"""
    from app.api.v1 import auth, users, doctors, appointments, medications, chat
    
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    return app

@pytest.fixture(scope="session")
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a new database session for a test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def override_get_db():
    """Override database dependency"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a test user"""
    user = User(
        id=str(uuid.uuid4()),
        email="testuser@example.com",
        password_hash=hash_password("oldpassword"),
        first_name="Test",
        last_name="User",
        role=UserRole.PATIENT,
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_doctor(db: Session) -> User:
    """Create a test doctor"""
    doctor = User(
        id=str(uuid.uuid4()),
        email="doctor@example.com",
        password_hash=hash_password("doctorpass"),
        first_name="Doctor",
        last_name="Test",
        role=UserRole.DOCTOR,
        is_active=True,
        email_verified=True,
        two_fa_enabled=True
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor

@pytest.fixture(scope="function")
def admin_user(db: Session) -> User:
    """Create a test admin user"""
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        password_hash=hash_password("adminpass"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def inactive_user(db: Session) -> User:
    """Create an inactive test user"""
    user = User(
        id=str(uuid.uuid4()),
        email="inactive@example.com",
        password_hash=hash_password("inactivepass"),
        first_name="Inactive",
        last_name="User",
        role=UserRole.PATIENT,
        is_active=False,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def unverified_user(db: Session) -> User:
    """Create an unverified test user"""
    user = User(
        id=str(uuid.uuid4()),
        email="unverified@example.com",
        password_hash=hash_password("unverifiedpass"),
        first_name="Unverified",
        last_name="User",
        role=UserRole.PATIENT,
        is_active=True,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(autouse=True)
def cleanup_database(db: Session):
    """Clean up the database after each test"""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
