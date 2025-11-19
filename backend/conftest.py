import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import app.core.redis_client as redis_module
from app.deps.auth import get_current_user

# DB de pruebas
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# Crear tablas
Base.metadata.create_all(bind=engine)


# Dependency override de la DB
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Fake user para test
def override_current_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password="fake_hash",
        role=UserRole.admin,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_current_user


# Agregar FakeRedis para tests
class FakeRedis:
    def __init__(self):
        self.store = {}
        self.connection_pool = None  # Mock connection pool

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def get(self, key):
        return self.store.get(key)

    async def mget(self, *keys):
        """Get multiple values at once"""
        return [self.store.get(key) for key in keys]

    async def delete(self, *keys):
        """Delete one or more keys"""
        for key in keys:
            if key in self.store:
                del self.store[key]

    async def ping(self):
        return True

    async def close(self):
        pass

    async def aclose(self):
        pass


# Dependencia para Redis en modo test
IS_TEST = os.environ.get("TESTING") == "1"

@pytest.fixture(autouse=True)
def fake_redis():
    redis = FakeRedis()
    redis_module.redis_client = redis
    yield
    redis_module.redis_client = None


# Fixture para el cliente de FastAPI
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
