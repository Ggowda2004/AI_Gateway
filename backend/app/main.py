from fastapi import FastAPI, Request, Depends
from routes.auth_r import router1
from routes.api_key import router2
# from routes.chat import router3
from routes.gateway import router4
from db.base_models import Base
from core.logging import logger
import json
from contextlib import asynccontextmanager
from services.redis_service import redis_service, get_redis
from core.config import settings
from redis.asyncio import Redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_service.initialize(settings.REDIS_URL)
        await logger.info("Application infrastructure startup complete.")
    except Exception as e:
        await logger.critical(f"Application failed to start: {str(e)}")
        raise e
    yield  # The server stays running
    
    # (Ctrl+C) mean server stop and redis closed
    await redis_service.close()
    await logger.info("Application infrastructure shutdown complete.")



app = FastAPI(
    title="AI Gateway",
    lifespan=lifespan#this registers the shutdown
)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.middleware("http")
# async def log_middleware(request: Request, call_next):
#     """Asynchronously logs every incoming HTTP request lifecycle."""
#     log_dict = {
#         "url": request.url.path,
#         "method": request.method,
#         "client_ip": request.client.host if request.client else "unknown"
#     }
#     #Non-blocking log for incoming request tracking
#     await logger.info(f"INBOUND  | {json.dumps(log_dict)}") #dict to json for clean output

#     response = await call_next(request)

#     await logger.info(f"OUTBOUND | URL: {request.url.path} | Status Code: {response.status_code}")
    
#     return response

# To prevent your logging middleware from buffering or blocking your real-time text event streams, you must explicitly check the URL path. If a user is hitting your streaming gateway route (/v1/chat/completions), let it pass through immediately without messing with the response object wrapper.


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    """Asynchronously logs every incoming HTTP request lifecycle, skipping body parsing for streams."""
    log_dict = {
        "url": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else "unknown"
    }
    
    # 1. Log the INBOUND connection normally
    await logger.info(f"INBOUND  | {json.dumps(log_dict)}")

    # 2. 🟢 FIXED: If it's your streaming gateway route, execute instantly and return!
    if request.url.path == "/v1/chat/completions":
        response = await call_next(request)
        # Log outbound directly since we shouldn't attempt to intercept streaming payloads
        await logger.info(f"OUTBOUND | URL: {request.url.path} | Status Code: {response.status_code} (STREAM)")
        return response

    # 3. Standard processing for regular JSON endpoints (like /healthz or auth routes)
    response = await call_next(request)
    await logger.info(f"OUTBOUND | URL: {request.url.path} | Status Code: {response.status_code}")
    
    return response


app.include_router(router1)
app.include_router(router2)
# app.include_router(router3)
app.include_router(router4)

@app.get("/")
async def check_health(redis_client: Redis = Depends(get_redis)):
    try:
        # Actually verify your infrastructure is alive in real time
        await redis_client.ping()
        return {
            "status": "healthy",
            "services": {
                "api": "online",
                "redis": "connected"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"Infrastructure dependency failure: {str(e)}"
        }

@app.get("/healthz")
def check_health():
    return {"message":"I guess things are working"}
