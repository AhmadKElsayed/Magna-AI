import asyncio
from ai_engine import generate_matching_image
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    print("Testing image generation via ai_engine.generate_matching_image...")
    print(f"Using OpenRouter Key: {'Loaded' if os.environ.get('OPENROUTER_API_KEY') else 'Missing'}")
    
    try:
        url = await generate_matching_image(
            topic="Cute Cats",
            tone="Playful",
            generated_text="Here is a wonderful blog post about cute cats playing with yarn!"
        )
        print("\n--- Success! ---")
        print("Image URL returned:")
        print(url)
    except Exception as e:
        print("\n--- Error during generation ---")
        print(e)

if __name__ == "__main__":
    asyncio.run(test())
