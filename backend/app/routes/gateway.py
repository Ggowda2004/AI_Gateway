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
from fastapi.responses import StreamingResponse
import json

router4 = APIRouter(
    prefix="/v1",
    tags=["AI Gateway"]
)

GEMINI_API_KEY = settings.GEMINI_API_KEY
GROQ_API_KEY = settings.GROQ_API_KEY 

# Note:removed response_model=GatewayResponse because streaming returns a raw event-stream text, not a flat JSON object.

@router4.post("/chat/completions", dependencies=[Depends(rate_limiter)])#response_model=GatewayResponse)
async def route_ai_request(
    request: GatewayRequest,
    req_context: Request,
    current_user: User = Security(get_user_from_api_key),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    #Checking Cache Layer First
    cache_key = generate_cache_key(request)
    cached_reply = await get_cached_response(redis_client, cache_key)
    
    if cached_reply:
        await logger.info(f"⚡ Cache HIT | Model: {request.model}")
        return cached_reply

    if request.model.startswith("gemini"):
        provider_name = "gemini"
        provider = GeminiProvider(api_key=GEMINI_API_KEY)
    elif request.model.startswith("llama") or request.model.startswith("mixtral"):
        provider_name = "groq"
        provider = GroqProvider(api_key=GROQ_API_KEY)
    else:
        await logger.error(f"Routing Failed | Model '{request.model}' is unsupported.")
        raise AuthError(f"Unsupported model provider: {request.model}")
    

    #Asynchronous Generator function with COMPLETE FALLBACK
    async def response_streamer():
        nonlocal provider_name, provider  # Allows us to swap them dynamically inside the generator
        full_response_text = ""
        start_time = time.perf_counter()
        status_label = "success"
        
        try:
            # Try to stream from primary provider
            async for chunk in provider.generate_stream(request):
                full_response_text += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                
        except Exception as primary_error:
            # ⚠️ Primary Stream Failed -> Initiate Fallback to Groq
            if provider_name == "gemini" and GROQ_API_KEY:
                await logger.error(
                    f"❌ Primary Stream 'gemini' Failed! Error: {str(primary_error)}. "
                    f"Initiating fallback streaming mechanism via Groq..."
                )
                try:
                    provider_name = "groq_fallback"
                    status_label = "fallback_success"
                    provider = GroqProvider(api_key=GROQ_API_KEY)
                    
                    # Restart streaming from the backup provider
                    async for chunk in provider.generate_stream(request):
                        full_response_text += chunk
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                        
                    await logger.info("✨ Fallback stream recovery successful via Groq!")
                except Exception as fallback_error:
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    await logger.error(f"🚨 Double Vendor Crash! Backup streaming failed: {str(fallback_error)}")
                    await handle_failed_log(db, req_context, current_user, request, latency_ms, "failed")
                    yield f"data: {json.dumps({'error': 'All upstream vendors failed'})}\n\n"
                    return
            else:
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                await handle_failed_log(db, req_context, current_user, request, latency_ms, "failed")
                yield f"data: {json.dumps({'error': 'Streaming interrupted'})}\n\n"
                return

        #(Only runs if a stream succeeded)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        api_key_record = req_context.state.api_key_record
        approx_tokens = len(full_response_text) // 4
        
        # Populate Redis Cache with complete text payload for next time
        response_payload = {
            "content": full_response_text,
            "model": request.model,
            "usage": {"prompt_tokens": 0, "completion_tokens": approx_tokens, "total_tokens": approx_tokens}
        }
        await set_cached_response(redis_client, cache_key, response_payload, ttl_seconds=3600)
        
        # Calculate dynamic cost tracking row
        if "groq" in provider_name:
            estimated_cost = approx_tokens * 0.00000008
        else:
            estimated_cost = approx_tokens * 0.0000003

        # Write Successful Log Row to PostgreSQL
        from models.audit_logs import AuditLogs
        db_log = AuditLogs(
            user_id=current_user.id,
            api_key_id=api_key_record.id,
            provider=provider_name,
            model=request.model,
            latency=latency_ms,
            prompt_tokens=0,
            total_tokens=approx_tokens,
            estimated_cost=round(estimated_cost, 7),
            status=status_label
        )
        db.add(db_log)
        await db.commit()
        await logger.info(f"Log written to DB for API Key ID: {api_key_record.id}")

    # 5. Return the live stream to client connection
    return StreamingResponse(response_streamer(), media_type="text/event-stream")


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