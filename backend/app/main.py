from fastapi import FastAPI
from routes.auth_r import router1
from routes.api_key import router2
from routes.chat import router3
from db.base_models import Base



app = FastAPI()
app.include_router(router1)
app.include_router(router2)
app.include_router(router3)


@app.get("/")
def home():
    return{"message":"next i will redirect this(pending work)"}

@app.get("/healthz")
def check_health():
    return {"message":"I guess things are working"}
