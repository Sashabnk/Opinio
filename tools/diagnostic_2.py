import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def check():
    url = "https://openapi.opinion.trade/openapi/market"
    headers = {"apikey": os.getenv("API_KEY")}
    params = {"page": 1, "pageSize": 1}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, params=params)
        print(r.json())

if __name__ == "__main__":
    asyncio.run(check())
