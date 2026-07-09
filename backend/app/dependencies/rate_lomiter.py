import time
from fastapi import Depends, HTTPException, status, Request
from redis.asyncio import Redis
from services.redis_service import get_redis
from core.logging import logger



LIMIT_PER_MINUTE = 5
async def rate_limiter(request: Request, redis_client: Redis = Depends(get_redis)):
    api_key_record = getattr(request.state, "api_key_record", None)
    if not api_key_record:
        return
    
    current_minute = time.strftime("%Y%m%d%H%M", time.gmtime())
    redis_key = f"ratelimit:{api_key_record.id}:{current_minute}"

    try:
        #Use an atomic pipeline to increment the count and set expiration
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(redis_key)
            pipe.expire(redis_key, 60)  # Key expires in 60s, cleaning up Redis automatically
            results = await pipe.execute()
        
        current_requests = results[0]  # The result of the INCR operation

        #Check if the user went over the limit
        if current_requests > LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"You have exceeded your limit of {LIMIT_PER_MINUTE} requests per minute.",
                    "retry_after_seconds": 60 - int(time.time() % 60)
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.info("Redis down, rate limiting or other redis works not possible")
        return