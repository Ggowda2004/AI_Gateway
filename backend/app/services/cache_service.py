import hashlib
import json
from redis.asyncio import Redis
from schemas.provider import GatewayRequest

# def generate_cache_key(request: GatewayRequest) -> str:
#     """Generates a stable unique MD5 hash based on model and prompt."""
#     # Convert request payload to a clean string format
#     request_dump = f"{request.model}:{json.dumps(request.messages, sort_keys=True)}"
#     prompt_hash = hashlib.md5(request_dump.encode("utf-8")).hexdigest()
#     return f"cache:{prompt_hash}"

def generate_cache_key(request: GatewayRequest) -> str:
    """Generates a stable unique MD5 hash based on model and prompt."""
    # 🟢 FIXED: Convert Pydantic message objects into plain dictionaries first
    serializable_messages = [msg.model_dump() for msg in request.messages]
    
    # Now json.dumps will run flawlessly without any TypeErrors
    request_dump = f"{request.model}:{json.dumps(serializable_messages, sort_keys=True)}"
    prompt_hash = hashlib.md5(request_dump.encode("utf-8")).hexdigest()
    return f"cache:{prompt_hash}"


async def get_cached_response(redis: Redis, cache_key: str) -> dict | None:
    """Looks up cached data in Redis."""
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None

async def set_cached_response(redis: Redis, cache_key: str, response_data: dict, ttl_seconds: int = 3600):
    """Saves a response to Redis with an expiration time (default 1 hour)."""
    await redis.setex(cache_key, ttl_seconds, json.dumps(response_data))
