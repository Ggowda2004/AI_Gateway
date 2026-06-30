from fastapi import FastAPI, Request
from routes.auth_r import router1
from routes.api_key import router2
from routes.chat import router3
from routes.gateway import router4
from db.base_models import Base
from core.logging import logger
import json


app = FastAPI()
app.include_router(router1)
app.include_router(router2)
app.include_router(router3)
app.include_router(router4)




@app.middleware("http")
async def log_middleware(request: Request, call_next):
    """Asynchronously logs every incoming HTTP request lifecycle."""
    log_dict = {
        "url": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else "unknown"
    }
    #Non-blocking log for incoming request tracking
    await logger.info(f"INBOUND  | {json.dumps(log_dict)}") #dict to json for clean output

    response = await call_next(request)

    await logger.info(f"OUTBOUND | URL: {request.url.path} | Status Code: {response.status_code}")
    
    return response


@app.get("/")
def home():
    return{"message":"next i will redirect this(pending work)"}

@app.get("/healthz")
def check_health():
    return {"message":"I guess things are working"}
