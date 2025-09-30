import requests, datetime as dt
import os
from dotenv import load_dotenv 


load_dotenv()
POLYGONE_KEY = os.getenv("POLYGONE_KEY")

API_KEY = POLYGONE_KEY

url = "https://api.polygon.io/v2/reference/news"
params = {
    "limit": 50,
    "apiKey": API_KEY
}
r = requests.get(url, params=params, timeout=15)
r.raise_for_status()
news = r.json()["results"]

# Each result has 'tickers' and 'published_utc'
newsTickers = [n["tickers"] for n in news]

hits = [(n["published_utc"], n.get("tickers", []), n["title"]) for n in news]



for news in newsTickers:
    for ticker in news:
        print(ticker)
