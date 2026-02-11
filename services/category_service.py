import re

class CategoryService:
    @staticmethod
    def get_category_hashtag(title: str) -> str:
        title_lower = title.lower()
        
        # Mapping from Website categories to keywords
        # Based on the user's screenshot: Macro, Pre-TGE, Crypto, Business, Politics, Sports, Tech, Culture
        categories = {
            "#Crypto": [
                "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "binance", 
                "cz", "crypto", "usdt", "usdc", "token", "blockchain", "altcoin",
                "memecoin", "pepe", "doge", "dex", "wallet", "metamask", "base", "ton"
            ],
            "#Politics": [
                "election", "trump", "harris", "biden", "president", "senate", 
                "government", "politics", "vote", "democrat", "republican", "white house"
            ],
            "#Macro": [
                "fed", "inflation", "cpi", "rate", "interest", "economy", 
                "gdp", "recession", "gold", "oil", "unemployment", "fomc"
            ],
            "#PreTGE": [
                "tge", "airdrop", "listing", "launch", "whitelist", "pre-market"
            ],
            "#Business": [
                "acquisition", "merger", "ceo", "startup", "stock", "ipo", "company",
                "revenue", "earnings", "valuation", "fdv"
            ],
            "#Tech": [
                "ai", "openai", "gpt", "nvidia", "tesla", "apple", "google", 
                "meta", "software", "hardware", "chip", "robot", "cloud"
            ],
            "#Sports": [
                "football", "soccer", "basketball", "nba", "nfl", "champion", 
                "match", "win", "league", "olympics", "final", "stadium"
            ],
            "#Culture": [
                "movie", "oscar", "music", "award", "celebrity", "grammy", 
                "film", "art", "fashion", "show"
            ]
        }
        
        for hashtag, keywords in categories.items():
            if any(re.search(rf"\b{keyword}\b", title_lower) for keyword in keywords):
                return hashtag
        
        # Default category if no match found
        return "#Opinion"
