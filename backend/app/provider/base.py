from abc import ABC, abstractmethod
from schemas.provider import GatewayRequest, GatewayResponse

class BaseAPIProvider(ABC):
    """
    Any new provider (OpenAI, Anthropic, etc.) MUST implement these methods.
    """
    @abstractmethod
    async def generate(self, request:GatewayRequest)->GatewayResponse:
        pass