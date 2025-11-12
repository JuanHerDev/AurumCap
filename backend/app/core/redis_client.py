from redis.asyncio import Redis
from dotenv import load_dotenv
import os
import logging
from typing import Optional

load_dotenv()

logger = logging.getLogger("app.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# If REQUIRE_REDIS is true (default), startup will raise when Redis is unavailable.
# Set REQUIRE_REDIS=false in development to allow the app to start without Redis.
REQUIRE_REDIS = os.getenv("REQUIRE_REDIS", "true").lower() == "true"

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
        if REQUIRE_REDIS:
            # In production we want to fail fast if Redis is required
            raise e
        else:
            # In development allow the app to continue without Redis
            logger.warning("Continuing without Redis because REQUIRE_REDIS is false.")
            return
    
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