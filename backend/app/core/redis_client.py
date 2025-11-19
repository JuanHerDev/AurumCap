from redis.asyncio import Redis
from dotenv import load_dotenv
import os
import logging
from typing import Optional

load_dotenv()

logger = logging.getLogger("app.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REQUIRE_REDIS = os.getenv("REQUIRE_REDIS", "true").lower() == "true"

# Singleton
redis_client: Optional[Redis] = Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)

async def connect_redis() -> None:
    global redis_client

    if redis_client is None:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

    try:
        await redis_client.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

        if REQUIRE_REDIS:
            raise e
        else:
            logger.warning("Continuing without Redis because REQUIRE_REDIS=false.")


async def close_redis() -> None:
    """
    Correct way to close redis.asyncio connections:
    - redis.close() → sync, no await
    - connection_pool.disconnect() → async, must await
    """
    global redis_client

    if redis_client:
        try:
            # Close the client (non-async)
            redis_client.close()

            # Properly close connection pool
            await redis_client.connection_pool.disconnect()

            logger.info("Redis connection closed.")
        except Exception:
            logger.exception("Error closing Redis connection.")
        finally:
            redis_client = None


def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized.")
    return redis_client


def get_redis_client() -> Redis:
    return get_redis()