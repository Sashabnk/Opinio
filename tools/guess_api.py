import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def try_endpoints():
    api_key = os.getenv("API_KEY")
    base_url = "https://openapi.opinion.trade/openapi"
    headers = {"apikey": api_key}
    
    endpoints = ["/tags", "/category", "/categories", "/market/tags"]
    
    async with httpx.AsyncClient() as client:
        for ep in endpoints:
            print(f"Checking {ep}...")
            r = await client.get(f"{base_url}{ep}", headers=headers)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                print(r.json())

if __name__ == "__main__":
    asyncio.run(try_endpoints())
