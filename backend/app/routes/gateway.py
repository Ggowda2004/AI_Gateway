from fastapi import APIRouter, Depends, status, Security, Request
from db.session import AsyncSession, get_db
from schemas.provider import GatewayRequest, GatewayResponse
from provider.gemini import GeminiProvider
from dependencies.api_key_dependency import get_user_from_api_key
from services.api_key_services import validate_api_key
from core.exceptions import AuthError
from core.config import settings
from core.logging import logger
import time
from models.users import User
from dependencies.rate_lomiter import rate_limiter
from services.redis_service import get_redis
from redis.asyncio import Redis
from services.cache_service import generate_cache_key, get_cached_response, set_cached_response


router4 = APIRouter(
    prefix="/v1",
    tags=["AI Gateway"]
)

GEMINI_API_KEY = settings.GEMINI_API_KEY
#rate limiter dependency added
@router4.post("/chat/completions", dependencies=[Depends(rate_limiter)], response_model=GatewayResponse)
async def route_ai_request(
    request: GatewayRequest,
    req_context: Request,
    current_user: User = Security(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
     redis_client: Redis = Depends(get_redis)#1
    ):

    cache_key = generate_cache_key(request)#2
    cached_reply = await get_cached_response(redis_client, cache_key)#3
    
    if cached_reply:
        await logger.info(f"⚡ Cache HIT | Model: {request.model}")
        return cached_reply # Fast return,

    # api_key_header = req_context.state.api_key_str
    if request.model.startswith("gemini"):
        provider_name = "gemini"
        provider = GeminiProvider(api_key=GEMINI_API_KEY) 
    else:
        logger.error(f"Routing Failed | Model '{request.model}' is unsupported.")

        raise AuthError(f"Unsupported model provider: {request.model}")

    # 3. Execute the payload through our unified interface contract

    start_time = time.perf_counter()
    try:
        response = await provider.generate(request)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        response_dict = response.model_dump() #4
        await set_cached_response(redis_client, cache_key, response_dict, ttl_seconds=3600)#5

        api_key_record = req_context.state.api_key_record

        prompt_tokens = response.usage.get('prompt_tokens', 0)
        completion_tokens = response.usage.get('completion_tokens', 0)
        total_tokens = prompt_tokens + completion_tokens

        estimated_cost = (prompt_tokens * 0.000000075) + (completion_tokens * 0.0000003)

        from models.audit_logs import AuditLogs
        db_log = AuditLogs(
            user_id=current_user.id,
            api_key_id=api_key_record.id,
            provider=provider_name,
            model=response.model,
            latency=latency_ms,  # Stored as integer ms
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
            estimated_cost=round(estimated_cost, 7),
            status="success"
        )

        db.add(db_log)
        await db.commit()  # Push permanently to PostgreSQL

        await logger.info(f"Log written to DB for API Key ID: {current_user.id}")
        return response
    except Exception as e:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        # Log crashes or vendor errors cleanly so you can audit them in logs/gateway.log

        from models.audit_logs import AuditLogs
        api_key_record = getattr(req_context.state, 'api_key_record', None)
        db_fail_log = AuditLogs(
            user_id=current_user.id if 'api_key_record' in locals() else None,
            api_key_id=api_key_record.id if 'api_key_record' in locals() else None,
            provider="gemini" if request.model.startswith("gemini") else "unknown",
            model=request.model,
            latency=latency_ms,
            prompt_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            status="failed"
        )
        db.add(db_fail_log)
        await db.commit()
        await logger.error(f"Upstream Failure | Model: {request.model} | Latency: {latency_ms:.2f}s | Error: {str(e)}")
        raise