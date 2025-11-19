import pytest
from unittest.mock import patch
from decimal import Decimal

# --- Mocks async correctos ---
async def fake_crypto_price(*args, **kwargs):
    return 60000

async def fake_stock_price(*args, **kwargs):
    return 200

async def fake_fundamentals(*args, **kwargs):
    return {"pe": 20}


def test_summary(client):
    # --- Registrar usuario de prueba ---
    client.post("/auth/register", json={
        "email": "summaryuser@example.com",
        "password": "password123",
        "full_name": "Summary User"
    })
    login_resp = client.post("/auth/login", json={
        "email": "summaryuser@example.com",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # --- Crear inversiones ---
    client.post("/investments", json={
        "symbol": "BTC",
        "asset_name": "Bitcoin",
        "asset_type": "crypto",
        "quantity": "1",
        "invested_amount": "50000"
    }, headers=headers)

    client.post("/investments", json={
        "symbol": "AAPL",
        "asset_name": "Apple",
        "asset_type": "stock",
        "quantity": "2",
        "invested_amount": "300"
    }, headers=headers)

    # --- Mock async de precios y fundamentals ---
    with patch("app.routers.investments.get_crypto_price", side_effect=fake_crypto_price), \
         patch("app.routers.investments.get_stock_price", side_effect=fake_stock_price), \
         patch("app.routers.investments.get_fundamentals", side_effect=fake_fundamentals):

        r = client.get("/investments/summary", headers=headers)
        assert r.status_code == 200

        data = r.json()

        # Valores esperados
        expected_current_value = Decimal("60000") + Decimal("2") * Decimal("200")  # 60400
        expected_total_invested = Decimal("50000") + Decimal("300")  # 50300
        expected_gain_loss = expected_current_value - expected_total_invested  # 10100
        expected_roi = (expected_gain_loss / expected_total_invested * Decimal("100")).quantize(Decimal("0.01"))

        assert Decimal(str(data["current_value"])) == expected_current_value
        assert Decimal(str(data["total_invested"])) == expected_total_invested
        assert Decimal(str(data["gain_loss"])) == expected_gain_loss
        assert Decimal(str(data["roi"])) == expected_roi

        items = {item["symbol"]: item for item in data["items"]}
        assert Decimal(str(items["BTC"]["current_price"])) == Decimal("60000")
        assert Decimal(str(items["BTC"]["current_value"])) == Decimal("60000")
        assert Decimal(str(items["AAPL"]["current_price"])) == Decimal("200")
        assert Decimal(str(items["AAPL"]["current_value"])) == Decimal("400")
        assert items["AAPL"]["fundamentals"] == {"pe": 20}
