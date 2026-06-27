from abc import ABC, abstractmethod
from schemas.provider import GatewayRequest, GatewayResponse

class BaseAPIProvider(ABC):
    """
    Any new provider (OpenAI, Anthropic, etc.) MUST implement these methods.
    """
    @abstractmethod
    async def generate(self, request:GatewayRequest)->GatewayResponse:
        pass


'''
This file defines the strict rulebook. Every provider file we make later must have an asynchronous generate method that accepts our GatewayRequest and outputs our GatewayResponse.
'''
