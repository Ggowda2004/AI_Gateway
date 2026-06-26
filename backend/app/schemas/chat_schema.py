from pydantic import BaseModel


class ChatRequest(BaseModel):
    msg:str



#currently this is a dummy response
class ChatResponse(BaseModel):
    status: str
    reply: str
    user_context: str
