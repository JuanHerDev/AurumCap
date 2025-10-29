from fastapi import APIRouter
import asyncio

router = APIRouter(
    prefix="/tests",
    tags=["Tests"]
)

@router.get("/test-error")
async def test_error():
    raise RuntimeError("Simulated backend error for Discord alert testing")

@router.get("/test-slow")
async def test_slow():
    await asyncio.sleep(3)  # Simulate a slow response
    return {"ok": True}