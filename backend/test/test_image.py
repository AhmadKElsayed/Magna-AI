import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv("d:/Projects/Magna-AI/backend/.env")

async def test_image():
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "bytedance-seed/seedream-4.5",
        "messages": [
            {"role": "user", "content": "A cute cat"}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60.0)
        print("Status Code:", response.status_code)
        try:
            print("Response:", response.json())
        except Exception as e:
            print("Text:", response.text)

if __name__ == "__main__":
    asyncio.run(test_image())
