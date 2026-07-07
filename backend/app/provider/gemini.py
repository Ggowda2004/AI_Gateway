# import httpx
# from provider.base import BaseAPIProvider
# from schemas.provider import GatewayRequest, GatewayResponse
# from core.security import AuthError
# import json


# class GeminiProvider(BaseAPIProvider):
#     def __init__(self, api_key: str):
#         if not api_key:
#             raise ValueError("Gemini API key is required")
#         self.api_key = api_key
#         self.base_url =  "https://generativelanguage.googleapis.com/v1beta"

#     # async def generate(self, request: GatewayRequest) -> GatewayResponse:
#     #     '''
#     #     Structure Nesting: Your schema passes a flat object ({"role": "user", "content": "hi"}). Google requires a nested structure with a parts array ({"role": "user", "parts": [{"text": "hi"}]}). This code converts your schema into Google's exact syntax.
#     #     '''
#     #     gemini_contents = []
#     #     for msg in request.messages:
#     #         role = "model" if msg.role == "assistant" else msg.role
#     #         gemini_contents.append({
#     #             "role": role,
#     #             "parts": [{"text": msg.content}]
#     #         })

#     #     payload = {
#     #     "contents": gemini_contents,
#     #     "generationConfig": {
#     #         "temperature": request.temperature,
#     #         }
#     #     }
#     #     if request.max_tokens:
#     #         payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
#     #         #Config Matching: It maps your schema's temperature and max_tokens variables into Google’s specific properties (temperature and maxOutputTokens).
#     #     url = f"{self.base_url}/models/{request.model}:generateContent?key={self.api_key}"

#     #     async with httpx.AsyncClient() as client:
#     #         try:
#     #             response = await client.post(url, json=payload, timeout=30.0)
                
#     #             if response.status_code != 200:
#     #                 raise AuthError(f"Gemini API error: {response.text}")
                
#     #             data = response.json()
#     #             # Safely extract values out from Gemini's nested response structure
#     #             ai_text = data["candidates"][0]["content"]["parts"][0]["text"]

#     #             # Extract token stats safely if provided by upstream vendor
#     #             usage_metadata = data.get("usageMetadata", {})
#     #             usage = {
#     #                 "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
#     #                 "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
#     #                 "total_tokens": usage_metadata.get("totalTokenCount", 0)#added default values to avoid KeyError if keys are missing
#     #             }
#     #             return GatewayResponse(
#     #                 content=ai_text,
#     #                 model=request.model,
#     #                 usage=usage
#     #             )
#     #         except Exception as e:
#     #             if isinstance(e, AuthError):
#     #                 raise
#     #             raise AuthError(f"Upstream provider connection failed: {str(e)}")

#     async def generate_stream(self, request: GatewayRequest):
#         """Asynchronously stream data tokens sequentially from raw Gemini HTTP endpoints."""
#         gemini_contents = []
#         for msg in request.messages:
#             role = "model" if msg.role == "assistant" else msg.role
#             gemini_contents.append({"role": role, "parts": [{"text": msg.content}]})

#         payload = {"contents": gemini_contents, "generationConfig": {"temperature": request.temperature}}
        
#         # 🟢 CHANGED: Swap route target identifier path to streamGenerateContent
#         url = f"{self.base_url}/models/{request.model}:streamGenerateContent?key={self.api_key}"

#         import httpx
#         # Use an httpx stream block to intercept tokens on the fly
#         async with httpx.AsyncClient() as client:
#             async with client.stream("POST", url, json=payload, timeout=30.0) as response:
#                 if response.status_code != 200:
#                     raise ValueError(f"Gemini streaming target initialization failed: {response.status_code}")
                
#                 async for line in response.aiter_lines():
#                     if not line or line.strip() == "" or line.startswith("[") or line.startswith("]"):
#                         continue
                    
#                     try:
#                         # Clean up formatting commas if Google wraps chunks in json list shapes
#                         clean_line = line.strip().rstrip(",")
#                         data = json.loads(clean_line)
#                         chunk_text = data["candidates"][0]["content"]["parts"][0]["text"]
#                         yield chunk_text
#                     except Exception:
#                         continue

#     async def generate(self, request: GatewayRequest) -> GatewayResponse:
#         """Satisfies the BaseAPIProvider abstract class interface by wrapping the stream."""
#         full_text = ""
#         # Simply consume the stream generator to build the full string
#         async for chunk in self.generate_stream(request):
#             full_text += chunk

#         # Return a valid unified GatewayResponse schema object
#         return GatewayResponse(
#             content=full_text,
#             model=request.model,
#             usage={"prompt_tokens": 0, "completion_tokens": len(full_text) // 4, "total_tokens": len(full_text) // 4}
#         )



#using inbuilt official SDK for Gemini instead of raw httpx calls to avoid parsing issues and improve reliability.

from google import genai
from google.genai import types
from schemas.provider import GatewayRequest, GatewayResponse

class GeminiProvider:
    """Unified implementation for upstream Gemini inference models using the official SDK."""
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required")
        # Initialize the official Google GenAI async client wrapper
        self.client = genai.Client(api_key=api_key)

    async def generate_stream(self, request: GatewayRequest):
        """Streams tokens cleanly using Google's official async engine client wrapper."""
        # Convert your messages into structures the official Google SDK expects
        gemini_messages = []
        for msg in request.messages:
            role = "model" if msg.role == "assistant" else msg.role
            gemini_messages.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg.content)])
            )

        # Call Google's official async streaming generator function
        # This replaces your manual url string builds and httpx line parsing loops!
        response_stream = await self.client.aio.models.generate_content_stream(
            model=request.model,
            contents=gemini_messages,
            config=types.GenerateContentConfig(temperature=request.temperature)
        )

        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text


    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """Satisfies the BaseAPIProvider abstract class interface by wrapping the stream."""
        full_text = ""
        # Simply consume the stream generator to build the full string
        async for chunk in self.generate_stream(request):
            full_text += chunk

        # Return a valid unified GatewayResponse schema object
        return GatewayResponse(
            content=full_text,
            model=request.model,
            usage={"prompt_tokens": 0, "completion_tokens": len(full_text) // 4, "total_tokens": len(full_text) // 4}
        )