from fastapi import APIRouter, Depends, status, Security, Request
from db.session import AsyncSession, get_db
from schemas.provider import GatewayRequest, GatewayResponse
from provider.gemini import GeminiProvider
from provider.groq import GroqProvider
from dependencies.api_key_dependency import get_user_from_api_key
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
GROQ_API_KEY = settings.GROQ_API_KEY  # Ensure GROQ_API_KEY is defined in core/config.py

@router4.post("/chat/completions", dependencies=[Depends(rate_limiter)], response_model=GatewayResponse)
async def route_ai_request(
    request: GatewayRequest,
    req_context: Request,
    current_user: User = Security(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    # 1. Check Cache Layer First
    cache_key = generate_cache_key(request)
    cached_reply = await get_cached_response(redis_client, cache_key)
    
    if cached_reply:
        await logger.info(f"⚡ Cache HIT | Model: {request.model}")
        return cached_reply

    # 2. Dynamic Router Core Setup
    if request.model.startswith("gemini"):
        provider_name = "gemini"
        provider = GeminiProvider(api_key=GEMINI_API_KEY)
    elif request.model.startswith("llama") or request.model.startswith("mixtral"):
        provider_name = "groq"
        provider = GroqProvider(api_key=GROQ_API_KEY)
    else:
        await logger.error(f"Routing Failed | Model '{request.model}' is unsupported.")
        raise AuthError(f"Unsupported model provider: {request.model}")

    start_time = time.perf_counter()
    status_label = "success"
    
    try:
        # 3. Execute Primary Vendor Request
        response = await provider.generate(request)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
    except Exception as primary_error:
        # ⚠️ 4. Failover Recovery Flow (If Gemini crashes, immediately swap to Groq)
        if provider_name == "gemini" and GROQ_API_KEY:
            await logger.error(
                f"❌ Primary Provider 'gemini' Failed! Error: {str(primary_error)}. "
                f"Initiating fallback failover mechanism to Groq..."
            )
            try:
                provider_name = "groq_fallback"
                status_label = "fallback_success"
                provider = GroqProvider(api_key=GROQ_API_KEY)
                
                response = await provider.generate(request)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                await logger.info("✨ Fallback recovery successful via Groq!")
            except Exception as fallback_error:
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                await logger.error(f"🚨 Double Vendor Crash! Backup provider also failed: {str(fallback_error)}")
                await handle_failed_log(db, req_context, current_user, request, latency_ms, "failed")
                raise fallback_error
        else:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            await handle_failed_log(db, req_context, current_user, request, latency_ms, "failed")
            raise primary_error

    # 5. Populate Cache Footprint
    response_dict = response.model_dump()
    await set_cached_response(redis_client, cache_key, response_dict, ttl_seconds=3600)

    # 6. Extract Consumption Metrics
    api_key_record = req_context.state.api_key_record
    prompt_tokens = response.usage.get('prompt_tokens', 0)
    completion_tokens = response.usage.get('completion_tokens', 0)
    total_tokens = prompt_tokens + completion_tokens

    # Dynamic Pricing Calculations (Groq Llama 3 models are significantly cheaper)
    if "groq" in provider_name:
        estimated_cost = (prompt_tokens * 0.00000005) + (completion_tokens * 0.00000008)  # Llama 3.1 8B rates
    else:
        estimated_cost = (prompt_tokens * 0.000000075) + (completion_tokens * 0.00000003) # Gemini 2.5 Flash rates

    # 7. Write Successful Audit Log Row to PostgreSQL
    from models.audit_logs import AuditLogs
    db_log = AuditLogs(
        user_id=current_user.id,
        api_key_id=api_key_record.id,
        provider=provider_name,
        model=response.model,
        latency=latency_ms,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
        estimated_cost=round(estimated_cost, 7),
        status=status_label
    )
    db.add(db_log)
    await db.commit()
    
    await logger.info(f"Log written to DB for API Key ID: {api_key_record.id}")
    return response


async def handle_failed_log(db: AsyncSession, req_context: Request, current_user: User, request: GatewayRequest, latency_ms: int, status: str):
    """Helper method to clean up repetitive database code loops inside exception scopes."""
    from models.audit_logs import AuditLogs
    api_key_record = getattr(req_context.state, 'api_key_record', None)
    db_fail_log = AuditLogs(
        user_id=current_user.id if current_user else None,
        api_key_id=api_key_record.id if api_key_record else None,
        provider="gemini" if request.model.startswith("gemini") else "groq",
        model=request.model,
        latency=latency_ms,
        prompt_tokens=0,
        total_tokens=0,
        estimated_cost=0.0,
        status=status
    )
    db.add(db_fail_log)
    await db.commit()