from redis.asyncio import Redis
from app.core.settings import settings

# Global Redis client - initialized on startup, closed on shutdown
redis_client: Redis | None = None

async def init_redis() -> None:
    """Initialized the Redis connection pool on app startup"""
    global redis_client
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    # Verify connection
    await redis_client.ping()
    print("[Redis] Connected successfully")

async def close_redis() -> None:
    """Close the Redis connection pool on app shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()
        print("[Redis] Connection closed")

def get_redis() -> Redis:
    """Returns the global Redis client. Must be called after init_redis()"""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized - call init_redis() first")
    return redis_client