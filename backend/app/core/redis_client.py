from redis.asyncio import Redis
from dotenv import load_dotenv
import os
import logging
from typing import Optional

load_dotenv()

logger = logging.getLogger("app.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Singleton client

redis_client: Optional[Redis] = Redis.from_url(REDIS_URL, decode_responses=True)

async def connect_redis() -> None:
    # Called on FastAPI to validate connection

    global redis_client
    
    if redis_client is None:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e
    
async def close_redis() -> None:
    # Close connection pool on shutdown

    global redis_client

    if redis_client:
        try:
            await redis_client.close()
            await redis_client.connection_pool.disconnect()
            logger.info("Redis connection closed.")
        except Exception:
            logger.exception("Error closing Redis connection.")
        finally:
            redis_client = None

# FastAPI dependency
def get_redis() -> Redis:
    # Dependency to get Redis client
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized.")
    return redis_client