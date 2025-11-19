def test_create_investment(client):
    payload = {
        "symbol": "AAPL",
        "asset_name": "Apple",
        "type": "stock",
        "quantity": "2",
        "invested_amount": "300"
    }

    r = client.post("/investments", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert data["quantity"] == "2"


def test_list_investments(client):
    r = client.get("/investments")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_investment(client):
    # Create first
    payload = {
        "symbol": "BTC",
        "asset_name": "Bitcoin",
        "type": "crypto",
        "quantity": "1",
        "invested_amount": "50000"
    }

    created = client.post("/investments", json=payload).json()
    inv_id = created["id"]

    r = client.get(f"/investments/{inv_id}")
    assert r.status_code == 200
    assert r.json()["symbol"] == "BTC"


def test_update_investment(client):
    created = client.post("/investments", json={
        "symbol": "TSLA",
        "asset_name": "Tesla",
        "type": "stock",
        "quantity": "3",
        "invested_amount": "900"
    }).json()

    inv_id = created["id"]

    r = client.patch(f"/investments/{inv_id}", json={"quantity": "4"})
    assert r.status_code == 200
    assert r.json()["quantity"] == "4"


def test_delete_investment(client):
    created = client.post("/investments", json={
        "symbol": "ETH",
        "asset_name": "Ethereum",
        "type": "crypto",
        "quantity": "0.5",
        "invested_amount": "1500"
    }).json()

    inv_id = created["id"]

    r = client.delete(f"/investments/{inv_id}")
    assert r.status_code == 204

    r2 = client.get(f"/investments/{inv_id}")
    assert r2.status_code == 404
