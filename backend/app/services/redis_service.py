from core.logging import logger
import redis.asyncio as aioredis
# @asynccontextmanager lets you wrap your setup and teardown logic into a single, highly readable function.


class RedisService:
    """Manages an optimized, safe asynchronous Redis lifecycle connection pool."""
    def __init__(self):
        self.client:aioredis.Redis | None = None
    
    async def initialize(self, redis_url: str):
        #global client structure
        await logger.info("Initializing global asynchronous Redis connection pool...")
        self.client = aioredis.from_url(
            redis_url, 
            decode_responses=True,
            max_connections=20
        )
        try:
            await self.client.ping()
            await logger.info("✅ Redis client successfully pinged and healthy.")
        except Exception as e:
            await logger.critical(f"❌ Redis connection health check failed! Error: {str(e)}")
            raise e

    async def close(self):
        #draining
        if self.client:
            await logger.info("Draining and terminating Redis connection pools...")
            await self.client.close()

redis_service = RedisService()

# Creating a reusable Redis service dependency injector
async def get_redis() -> aioredis.Redis:
    """FastAPI Injection target supplying active authenticated clients."""
    if redis_service.client is None:
        raise RuntimeError("Redis Client requested before subsystem initialization.")
    return redis_service.client