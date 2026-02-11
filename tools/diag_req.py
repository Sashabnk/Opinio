import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
url = f"https://openapi.opinion.trade/openapi/market/3721"
headers = {"apikey": api_key}

response = requests.get(url, headers=headers)
print(response.status_code)
print(response.json())
