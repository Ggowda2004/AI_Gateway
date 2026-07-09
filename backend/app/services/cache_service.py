# async caching layer fro llm api request

import hashlib
import json
from redis.asyncio import Redis
from schemas.provider import GatewayRequest

def generate_cache_key(request: GatewayRequest) -> str:
    #Convert Pydantic message objects into plain dictionaries first
    serializable_messages = [msg.model_dump() for msg in request.messages]
    request_dump = f"{request.model}:{json.dumps(serializable_messages, sort_keys=True)}"
    prompt_hash = hashlib.md5(request_dump.encode("utf-8")).hexdigest()
    return f"cache:{prompt_hash}"


async def get_cached_response(redis: Redis, cache_key: str) -> dict | None:
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None

async def set_cached_response(redis: Redis, cache_key: str, response_data: dict, ttl_seconds: int = 3600):
    await redis.setex(cache_key, ttl_seconds, json.dumps(response_data))


# This code creates an asynchronous LLM caching layer by generating deterministic MD5 keys from structured Pydantic requests. It uses atomic Redis operations to store and fetch serialized responses with custom expirations.