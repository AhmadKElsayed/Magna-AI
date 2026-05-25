import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test():
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Magna AI Suite"
    }
    data = {
        "model": "black-forest-labs/flux.2-klein-4b",
        "messages": [
            {"role": "user", "content": "A cute cat playing with yarn"}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        print("Status:", resp.status_code)
        try:
            print("Response:", resp.json())
        except:
            print("Text:", resp.text)

if __name__ == "__main__":
    asyncio.run(test())
