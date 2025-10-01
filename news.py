import requests, datetime as dt
import os
from dotenv import load_dotenv 
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()
POLYGONE_KEY = os.getenv("POLYGONE_KEY")

API_KEY = POLYGONE_KEY

now = dt.datetime.utcnow()
since = (now - dt.timedelta(hours=2)).isoformat(timespec="seconds") + "Z" 

url = "https://api.polygon.io/v2/reference/news"
params = {
    "published_utc.gte": since,   # filter to “just got news”
    "limit": 1000,
    "apiKey": API_KEY
}
r = requests.get(url, params=params, timeout=15)
r.raise_for_status()
news = r.json()["results"]

# Each result has 'tickers' and 'published_utc'
hits = [(n["published_utc"], n.get("tickers", []), n["title"]) for n in news]
for ts, tickers, title in hits:
    dt_utc = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    dt_et = dt_utc.astimezone(ZoneInfo("America/New_York"))
    
    if dt_et.minute in (30, 0):
        print(dt_et, tickers, title)

