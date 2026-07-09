from fastapi import FastAPI, Request, Depends
from routes.auth_r import router1
from routes.api_key import router2
from routes.gateway import router4
from db.base_models import Base
from core.logging import logger
import json
from contextlib import asynccontextmanager
from services.redis_service import redis_service, get_redis
from core.config import settings
from redis.asyncio import Redis
from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager #This decorator turns a standard generator function into an asynchronous context manager.
async def lifespan(app: FastAPI):
    try:
        await redis_service.initialize(settings.REDIS_URL)
        await logger.info("Application infrastructure startup complete.")
    except Exception as e:
        await logger.critical(f"Application failed to start: {str(e)}")
        raise e
    yield  # The server starts running after this point, and the code after yield will execute when the server is shutting down.
    
    #mean server stop and redis closed
    await redis_service.close()
    await logger.info("Application infrastructure shutdown complete.")



app = FastAPI(
    title="AI Gateway",
    lifespan=lifespan #for startup and shutdown events
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_middleware(request: Request, call_next):
    """Asynchronously logs every incoming HTTP request lifecycle, skipping streams."""
    log_dict = {
        "url": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else "unknown"
    }
    
    #Non-blocking log for incoming request tracking
    await logger.info(f"INBOUND  | {json.dumps(log_dict)}")

    #Special handling for straming endpoints
    if request.url.path == "/v1/chat/completions":
        response = await call_next(request)
        #we shouldn't attempt to intercept streaming payloads
        await logger.info(f"OUTBOUND | URL: {request.url.path} | Status Code: {response.status_code} (STREAM)")
        return response

    #non-streaming endpoints
    response = await call_next(request)
    await logger.info(f"OUTBOUND | URL: {request.url.path} | Status Code: {response.status_code}")
    return response


app.include_router(router1)
app.include_router(router2)
app.include_router(router4)

@app.get("/")
async def check_health(redis_client: Redis = Depends(get_redis)):
    try:
        #Verify your infrastructure is alive in real time
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
    
