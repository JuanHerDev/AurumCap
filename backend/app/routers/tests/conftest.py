import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.core.redis_client import get_redis_client

# ---------------------------------------------------------------------
# TEST DATABASE (SQLite en memoria)
# ---------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ---------------------------------------------------------------------
# FIXTURE: resetear la BD **una vez por test**
# ---------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

# ---------------------------------------------------------------------
# OVERRIDE DB
# ---------------------------------------------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# ---------------------------------------------------------------------
# MOCK REDIS (FakeRedis en memoria)
# ---------------------------------------------------------------------
class FakeRedis:
    async def get(self, key): return None
    async def set(self, key, value, ex=None): return True
    async def delete(self, key): return True
    async def close(self): pass

@pytest.fixture
def fake_redis():
    return FakeRedis()

@pytest.fixture(autouse=True)
def override_redis(fake_redis):
    async def _override():
        return fake_redis
    app.dependency_overrides[get_redis_client] = _override
    yield
    app.dependency_overrides.pop(get_redis_client, None)

# ---------------------------------------------------------------------
# CLIENT SYNC (para la mayoría de tests)
# ---------------------------------------------------------------------
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# ---------------------------------------------------------------------
# CLIENT ASYNC (para refresh token tests)
# ---------------------------------------------------------------------
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    """
    Mock de Redis compatible con todas las llamadas usadas en la app.
    """

    class FakeRedis:
        def __init__(self):
            self.storage = {}
            self.expire_times = {}

        async def get(self, key):
            return self.storage.get(key)

        async def set(self, key, value, ex=None, px=None, nx=False, xx=False, keepttl=False):
            self.storage[key] = value
            return True

        async def delete(self, *keys):
            for k in keys:
                self.storage.pop(k, None)
            return True

        async def mget(self, keys):
            return [self.storage.get(k) for k in keys]

        async def ping(self):
            return True

        async def close(self):
            return True

        @property
        def connection_pool(self):
            class DummyPool:
                async def disconnect(self_inner):
                    return True
            return DummyPool()

    fake = FakeRedis()

    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: fake)
    monkeypatch.setattr("app.core.redis_client.redis_client", fake)

    yield
