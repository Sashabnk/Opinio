
import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional
from core.config import config

logger = logging.getLogger(__name__)

class OpinionAPIService:
    def __init__(self, api_key: str = config.API_KEY, base_url: str = config.API_BASE_URL):
        self.base_url = base_url
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }

    async def get_markets(self, 
                          page: int = 1, 
                          page_size: int = 50, 
                          status: str = "activated", 
                          sort_order: int = 1) -> List[Dict[str, Any]]:
        """Fetch markets from Opinion API (Binary type 0, Multi type 1, and Other type 2)."""
        all_markets = []
        # Types represent different categories of markets in Opinion.trade
        # Type 1 (Multi), 0 (Single), 2 (Other), 3 (Trending/New)
        # We fetch multiple pages because the API seems to cap at 10 items per request.
        # Increased to 10 pages (100 items per type) to ensure no events are missed under heavy load.
        for mt in [1, 0, 2, 3]:
            for p in range(1, 11): 
                url = f"{self.base_url}/market"
                params = {
                    "page": p,
                    "pageSize": 10, # Explicitly use 10 since it's the limit
                    "status": status,
                    "marketType": mt,
                    "sort": sort_order
                }
                
                async with httpx.AsyncClient(timeout=20.0) as client:
                    try:
                        response = await client.get(url, headers=self.headers, params=params)
                        response.raise_for_status()
                        data = response.json()
                        
                        if data.get("errno") == 0:
                            result = data.get("result", {})
                            if isinstance(result, dict):
                                m_list = result.get("list", [])
                                if not m_list:
                                    break # No more markets for this type
                                all_markets.extend(m_list)
                                if len(m_list) < 10:
                                    break # Last page
                        else:
                            logger.error(f"API Error for type {mt} page {p}: {data}")
                            break
                    except Exception as e:
                        logger.error(f"Request failed for type {mt} page {p}: {e}")
                        break
                # Tiny delay to avoid overwhelming the API
                await asyncio.sleep(0.1)
        
        # Deduplicate markets by ID
        seen_ids = set()
        unique_markets = []
        for m in all_markets:
            mid = m.get("marketId")
            if mid and mid not in seen_ids:
                unique_markets.append(m)
                seen_ids.add(mid)
        
        return unique_markets



    async def get_token_price(self, token_id: str, market_id: Optional[str] = None) -> Optional[float]:
        """Fetch the latest price for a token with fallback to Topic API for Hourly markets."""
        # Try Open API first
        url = f"{self.base_url}/token/latest-price"
        params = {"token_id": token_id}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                if data.get("errno") == 0:
                    result = data.get("result", {})
                    price_str = result.get("price")
                    if price_str and float(price_str) > 0:
                        return float(price_str)
            except Exception as e:
                logger.error(f"Failed to fetch price from Open API for {token_id}: {e}")

        # Fallback to Topic API (Proxy) if market_id is provided and price was 0 or failed
        if market_id:
            try:
                # The Proxy API often has fresher price data for new types like 'Hourly'
                proxy_url = f"https://proxy.opinion.trade:8443/api/bsc/api/v2/topic/{market_id}"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(proxy_url)
                    if response.status_code == 200:
                        data = response.json()
                        res = data.get("result", {}).get("data", {})
                        # logger.info(f"DEBUG Topic Proxy: yesPos={res.get('yesPos')} vs token_id={token_id}")
                        # Check if token matches yesPos or noPos
                        if str(res.get("yesPos")) == str(token_id):
                            return float(res.get("yesMarketPrice") or 0)
                        elif str(res.get("noPos")) == str(token_id):
                            return float(res.get("noMarketPrice") or 0)
            except Exception as e:
                logger.error(f"Fallback Topic API failed for market {market_id}: {e}")
        
        return None

    def get_trade_url(self, market_id: str, is_multi: bool = False) -> str:
        """Generate URL for a market detail page."""
        url = f"https://app.opinion.trade/detail?topicId={market_id}"
        if is_multi:
            url += "&type=multi"
        return url
