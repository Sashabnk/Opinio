import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def check_market_detail(market_id):
    api_key = os.getenv("API_KEY")
    # Trying both possible detail endpoints based on documentation chunks seen earlier
    # Chunk 4 mentioned /market/{marketId}
    url = f"https://openapi.opinion.trade/openapi/market/{market_id}"
    headers = {"apikey": api_key}
    
    async with httpx.AsyncClient() as client:
        print(f"--- Fetching detail for market {market_id} ---")
        response = await client.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print(response.text)

if __name__ == "__main__":
    # Using IDs from previous user logs
    asyncio.run(check_market_detail(3721))
