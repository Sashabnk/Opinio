import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def check_keys():
    api_key = os.getenv("API_KEY")
    url = "https://openapi.opinion.trade/openapi/market"
    headers = {"apikey": api_key}
    params = {"pageSize": 1}
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, params=params)
        data = r.json()
        if data['errno'] == 0 and data['result']['list']:
            market = data['result']['list'][0]
            print(f"Keys in market object: {list(market.keys())}")
            # Also fetch detail for the same market
            m_id = market['marketId']
            r_detail = await client.get(f"https://openapi.opinion.trade/openapi/market/{m_id}", headers=headers)
            detail = r_detail.json()
            if detail['errno'] == 0:
                print(f"Keys in detail object: {list(detail['result']['data'].keys())}")
        else:
            print("No markets found.")

if __name__ == "__main__":
    asyncio.run(check_keys())
