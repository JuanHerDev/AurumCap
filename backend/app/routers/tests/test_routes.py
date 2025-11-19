from fastapi import APIRouter
import asyncio

router = APIRouter(
    prefix="/tests",
    tags=["Tests"]
)

def test_error(client):
    response = client.get("/test-error")
    assert response.status_code == 500

@router.get("/test-slow")
async def test_slow():
    await asyncio.sleep(3)  # Simulate a slow response
    return {"ok": True}