import httpx
from provider.base import BaseAPIProvider
from schemas.provider import GatewayRequest, GatewayResponse
from core.security import AuthError


class GeminiProvider(BaseAPIProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required")
        self.api_key = api_key
        self.base_url =  "https://generativelanguage.googleapis.com/v1beta"

    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        '''
        Structure Nesting: Your schema passes a flat object ({"role": "user", "content": "hi"}). Google requires a nested structure with a parts array ({"role": "user", "parts": [{"text": "hi"}]}). This code converts your schema into Google's exact syntax.
        '''
        gemini_contents = []
        for msg in request.messages:
            role = "model" if msg.role == "assistant" else msg.role
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "temperature": request.temperature,
            }
        }
        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
            #Config Matching: It maps your schema's temperature and max_tokens variables into Google’s specific properties (temperature and maxOutputTokens).
        url = f"{self.base_url}/models/{request.model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                
                if response.status_code != 200:
                    raise AuthError(f"Gemini API error: {response.text}")
                
                data = response.json()
                # Safely extract values out from Gemini's nested response structure
                ai_text = data["candidates"][0]["content"]["parts"][0]["text"]

                # Extract token stats safely if provided by upstream vendor
                usage_metadata = data.get("usageMetadata", {})
                usage = {
                    "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                    "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                    "total_tokens": usage_metadata.get("totalTokenCount", 0)#added default values to avoid KeyError if keys are missing
                }
                return GatewayResponse(
                    content=ai_text,
                    model=request.model,
                    usage=usage
                )
            except Exception as e:
                if isinstance(e, AuthError):
                    raise
                raise AuthError(f"Upstream provider connection failed: {str(e)}")