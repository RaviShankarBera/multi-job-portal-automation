from typing import Optional

from app.core.config import settings

redis_client = None


async def get_redis():
    """Get Redis client. Returns None if Redis is not configured."""
    global redis_client
    if not settings.REDIS_URL:
        return None
    try:
        import redis.asyncio as aioredis
        if redis_client is None:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return redis_client
    except Exception:
        return None


async def close_redis() -> None:
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
        except Exception:
            pass
        redis_client = None
