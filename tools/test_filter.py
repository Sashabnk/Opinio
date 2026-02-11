import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_tag_filter():
    api_key = os.getenv("API_KEY")
    url = "https://openapi.opinion.trade/openapi/market"
    headers = {"apikey": api_key}
    
    # Try filtering by Crypto
    params_crypto = {"tags": "Crypto", "pageSize": 1}
    # Try filtering by a tag that shouldn't match (e.g., Macro)
    params_macro = {"tags": "Macro", "pageSize": 1}
    
    async with httpx.AsyncClient() as client:
        r1 = await client.get(url, headers=headers, params=params_crypto)
        r2 = await client.get(url, headers=headers, params=params_macro)
        
        print(f"Total with tags=Crypto: {r1.json()['result']['total']}")
        print(f"Total with tags=Macro: {r2.json()['result']['total']}")

if __name__ == "__main__":
    asyncio.run(test_tag_filter())
