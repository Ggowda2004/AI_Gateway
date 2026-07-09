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
        return GatewayResponse(
            content=full_text,
            model=request.model,
            usage={"prompt_tokens": 0, "completion_tokens": len(full_text) // 4, "total_tokens": len(full_text) // 4}
        )
        


# This code implements a unified asynchronous client wrapper for Google's Gemini models using the official genai SDK. It converts standardized gateway requests into SDK-compatible structures, handles asynchronous streaming token-by-token using generate_content_stream, and provides a fallback method to accumulate streamed chunks into a single, structured object response with token usage estimations.