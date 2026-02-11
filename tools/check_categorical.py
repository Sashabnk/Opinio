import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def check_categorical():
    api_key = os.getenv("API_KEY")
    url = "https://openapi.opinion.trade/openapi/market"
    headers = {"apikey": api_key}
    params = {"page": 1, "pageSize": 5, "status": "activated", "type": 1, "sort": 1}
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, params=params)
        print("Categorical markets:")
        print(r.json())

if __name__ == "__main__":
    asyncio.run(check_categorical())
