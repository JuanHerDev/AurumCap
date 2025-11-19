import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.core.redis_client import redis_client

# Fixture para mockear Redis
@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    monkeypatch.setattr(redis_client.__class__, "ping", mock.ping)
    monkeypatch.setattr(redis_client.__class__, "get", mock.get)
    monkeypatch.setattr(redis_client.__class__, "set", mock.set)

# Fixture para AsyncClient
@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac

@pytest.mark.asyncio
async def test_refresh_token(client):
    # Crear email único para evitar conflictos
    email = f"refreshtest-{uuid.uuid4()}@example.com"
    password = "securepassword123"

    # Registrar usuario
    resp = await client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Refresh Test User"
    })
    assert resp.status_code == 200

    # Login para obtener tokens
    login_resp = await client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200
    refresh_cookie = login_resp.cookies.get("aurum_refresh_token")
    assert refresh_cookie is not None

    # Hacer refresh con cookie
    headers = {"Cookie": f"aurum_refresh_token={refresh_cookie}"}
    refresh_resp = await client.post("/auth/refresh", headers=headers)
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()
    assert isinstance(refresh_resp.json()["access_token"], str)
