from groq import AsyncGroq
from schemas.provider import GatewayRequest, GatewayResponse

class GroqProvider:
    """Unified implementation for upstream Groq inference models."""
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Groq API key is required")
        # Initialize the official async Groq SDK client
        self.client = AsyncGroq(api_key=api_key)

    # async def generate(self, request: GatewayRequest) -> GatewayResponse:
    #     """Executes the standard incoming contract against Groq endpoints."""
    #     # 🟢 Failover Rule: If the user requested a 'gemini' model but hit this provider,
    #     # route it automatically to Groq's high-speed Llama models
    #     target_model = "llama-3.3-70b-versatile" if request.model.startswith("gemini") else request.model

    #     # Extract values into standard message structures that Groq/OpenAI expect
    #     groq_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    #     # Call the asynchronous text generation endpoint
    #     response = await self.client.chat.completions.create(
    #         model=target_model,
    #         messages=groq_messages,
    #         temperature=request.temperature or 0.7,
    #         max_completion_tokens=request.max_tokens  # Groq prefers max_completion_tokens
    #     )

    #     # 🟢 Map the response to your strict, flat GatewayResponse schema
    #     return GatewayResponse(
    #         content=response.choices[0].message.content,  # Fixed choice list extraction
    #         model=response.model,
    #         usage={
    #             "prompt_tokens": response.usage.prompt_tokens,
    #             "completion_tokens": response.usage.completion_tokens,
    #             "total_tokens": response.usage.total_tokens
    #         }
    #     )

    async def generate_stream(self, request: GatewayRequest):
        """Asynchronously stream data tokens sequentially from Groq Endpoints."""
        target_model = "llama-3.3-70b-versatile" if request.model.startswith("gemini") else request.model
        groq_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Call the SDK with stream=True enabled
        response_stream = await self.client.chat.completions.create(
            model=target_model,
            messages=groq_messages,
            temperature=request.temperature or 0.7,
            stream=True  # 🟢 Tells Groq to return chunks iteratively
        )

        async for chunk in response_stream:
            # Extract content string token delta blocks
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate(self, request: GatewayRequest) -> GatewayResponse:
        """Satisfies the BaseAPIProvider abstract class interface by wrapping the stream."""
        full_text = ""
        async for chunk in self.generate_stream(request):
            full_text += chunk

        return GatewayResponse(
            content=full_text,
            model="llama-3.3-70b-versatile" if request.model.startswith("gemini") else request.model,
            usage={"prompt_tokens": 0, "completion_tokens": len(full_text) // 4, "total_tokens": len(full_text) // 4}
        )
