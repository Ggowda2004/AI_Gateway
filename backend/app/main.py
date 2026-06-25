from fastapi import FastAPI
from api.auth_r import router1
from api.api_key import router2
from db.base_models import Base



app = FastAPI()
app.include_router(router1)
app.include_router(router2)


@app.get("/")
def home():
    return{"message":"next i will redirect this(pending work)"}

@app.get("/healthz")
def check_health():
    return {"message":"I guess things are working"}
