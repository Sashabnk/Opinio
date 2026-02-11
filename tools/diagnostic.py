import asyncio
import httpx
from core.config import config

async def check_detail(market_id):
    url = f"{config.API_BASE_URL}/market/{market_id}"
    headers = {"apikey": config.API_KEY}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        print(f"Detail for {market_id}:")
        print(r.json())

if __name__ == "__main__":
    asyncio.run(check_detail(3721))
