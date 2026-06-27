from fastapi import APIRouter, Depends, status, Security
from db.session import AsyncSession, get_db
from schemas.provider import GatewayRequest, GatewayResponse
from provider.gemini import GeminiProvider
from dependencies.api_key_dependency import get_user_from_api_key
from services.api_key_services import validate_api_key
from core.exceptions import AuthError
from core.config import settings

router4 = APIRouter(
    prefix="/v1",
    tags=["AI Gateway"]
)

GEMINI_API_KEY = settings.GEMINI_API_KEY

@router4.post("/chat/completions", response_model=GatewayResponse)
async def route_ai_request(request: GatewayRequest,
    api_key_header: str = Security(get_user_from_api_key),
    db: AsyncSession = Depends(get_db)):
    if not api_key_header:
        raise AuthError("API Key header is missing")
    """
    Unified Gateway Entrypoint.
    1. Authenticates the client token via your secure prefix-lookup system.
    2. Dynamically routes the payload to the correct upstream AI vendor.
    """
    # 1. Authenticate the incoming request using your optimized code
    # user = await validate_api_key(db, api_key_header)
    # if not user:
    #     raise AuthError("Unauthorized gateway access") -> already handled in api_key dependency

    # 2. Dynamic Router / Factory Pattern
    # Check what model the user wants. If it starts with 'gemini', use Gemini.
    if request.model.startswith("gemini"):
        provider = GeminiProvider(api_key=GEMINI_API_KEY)
    
    # This architecture makes adding OpenAI later as simple as adding an elif:
    # elif request.model.startswith("gpt"):
    #     provider = OpenAIProvider(api_key=OPENAI_API_KEY)
    
    else:
        raise AuthError(f"Unsupported model provider: {request.model}")

    # 3. Execute the payload through our unified interface contract
    response = await provider.generate(request)
    return response