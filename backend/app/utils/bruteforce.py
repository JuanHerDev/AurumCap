import os
import asyncio
from datetime import timedelta
from redis.asyncio import Redis
from dotenv import load_dotenv
from app.utils.discord_alerts import send_discord_alert
from typing import Optional

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

MAX_ATTEMPTS = int(os.getenv("BF_MAX_ATTEMPTS", 5)) # 5 attempts
WINDOW_SECONDS = int(os.getenv("BF_WINDOW_SECONDS", 300)) # 5 minutes
BLOCK_SECONDS = int(os.getenv("BF_BLOCK_SECONDS", 900)) # 15 minutes

# Prexifes for keys
def _counter_key(scope: str, value: str) -> str:
    return f"bf:count:{scope}:{value}"

def _block_key(scope: str, value: str) -> str:
    return f"bf:block:{scope}:{value}"

async def is_blocked(ip: Optional[str] = None, identifier: Optional[str] = None, redis: Optional[Redis] = None) -> bool:
    # Verify if ip or identifier is blocked

    if redis is None:
        raise RuntimeError("Redis client is required")
    
    keys = []

    if ip:
        keys.append(_block_key("ip", ip))
    if identifier:
        keys.append(_block_key("id", identifier))

    if not keys:
        return False
    
    # Verify if any key exists
    results = await redis.mget(*keys)
    return any(results)


async def record_failed_attempt(ip: Optional[str] = None, identifier: Optional[str] = None, redis: Optional[Redis] = None, request=None) -> int:
    # Record a failed login attempt for ip and/or identifier
    # If limit exceeded, set block key and send alert to discord

    if redis is None:
        raise RuntimeError("Redis client is required")
    
    async def _incr_and_check(scope: str, value: str):
        counter_key = _counter_key(scope, value)
        block_key = _block_key(scope, value)

        # Increment counter
        val = await redis.incr(counter_key)

        await redis.expire(counter_key, WINDOW_SECONDS)

        # If exceeded, set block
        if val >= MAX_ATTEMPTS:
            await redis.set(block_key, "1", ex=BLOCK_SECONDS)
            msg = f"**Bruteforce Alert**\nScope: {scope}\nValue: {value}\nAttempts: {val}\nBlocked for {BLOCK_SECONDS // 60} minutes."
            await send_discord_alert(
                title="Bruteforce Attack Detected",
                message=msg,
                level="critical"
            )
        return val
    
    counts = []

    if ip:
        counts.append(await _incr_and_check("ip", ip))
    if identifier:
        counts.append(await _incr_and_check("id", identifier))

    return max(counts) if counts else 0

async def reset_attempts(ip: Optional[str] = None, identifier: Optional[str] = None, redis: Optional[Redis] = None):
    # Reset failed attempts for ip and/or identifier

    if redis is None:
        raise RuntimeError("Redis client is required")
    
    keys = []

    if ip:
        keys += [_counter_key("ip", ip), _block_key("ip", ip)]
    if identifier:
        keys += [_counter_key("id", identifier), _block_key("id", identifier)]

    if keys:
        await redis.delete(*keys)