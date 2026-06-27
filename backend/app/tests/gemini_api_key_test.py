import asyncio
import httpx
from core.config import settings


# 🔑 PASTE YOUR GEMINI API KEY HERE TO TEST
GEMINI_API_KEY = settings.GEMINI_API_KEY

async def test_simple_gemini_call():
    # Use gemini-2.5-flash as gemini-1.5-flash is retired on the v1beta endpoint
    model_name = "gemini-2.5-flash"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # Strictly matching Google's expected JSON format
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "How many days are in a week?"}
                ]
            }
        ]
    }
    
    print(f"📡 Sending simple text generation request to {model_name}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            
            if response.status_code != 200:
                print(f"❌ Error Status {response.status_code}: {response.text}")
                return
                
            data = response.json()
            
            # Simple extraction of the plain text reply
            ai_reply = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\n🤖 AI Reply:\n{ai_reply}")
            
        except Exception as e:
            print(f"💥 Request failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_simple_gemini_call())
