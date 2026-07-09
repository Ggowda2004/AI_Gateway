from core.logging import logger
import redis.asyncio as aioredis
class RedisService:
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
        if self.client:
            await logger.info("Draining and terminating Redis connection pools...")
            await self.client.close()

redis_service = RedisService()

# Creating a reusable Redis service dependency injector
async def get_redis() -> aioredis.Redis:
    if redis_service.client is None:
        raise RuntimeError("Redis Client requested before subsystem initialization.")
    return redis_service.client


# This asynchronous Redis manager initializes a 20-client connection pool with auto-decoding. It executes a startup ping to fail fast if offline and provides a secure dependency injector for FastAPI routes.