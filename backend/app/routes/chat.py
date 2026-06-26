from fastapi import APIRouter, Depends, status
from dependencies.api_key_dependency import get_user_from_api_key
# from dependencies.api_key_dependency import get_current_api_key_context
from models.api_keys import APIKey
from models.users import User
from schemas.chat_schema import ChatRequest, ChatResponse

'''The below endpoint was a temp endpoint, to verify usage'''
# router3 = APIRouter(
#     prefix="/services",
#     tags=["Third-Party Services"]
#     )


# @router3.get("/data-stream")
# async def secure_data_stream(api_context: APIKey = Depends(get_current_api_key_context))->dict: # 👈 Guarded by API key!
#     key_owner = api_context.user 
    
#     return {
#         "status": "authenticated",
#         "authenticated_via_key": api_context.name,
#         "key_id": api_context.id,
#         "owner_email": key_owner.email
#     }


router3 = APIRouter(
    prefix="/chat",
    tags=["AI Chat Assistant"]
    )

@router3.post(
    "/", 
    response_model=ChatResponse,
    summary="Send a message to the AI Chat assistant",
    status_code=status.HTTP_200_OK
)
async def placeholder_chat_endpoint(
    payload: ChatRequest,current_user: User = Depends(get_user_from_api_key)
):
    return {
        "status": "success",
        "reply": f"This is a placeholder AI response to your message: '{payload.msg}'",
        "user_context": f"Authenticated via user account: {current_user.email}"
    }