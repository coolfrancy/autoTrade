import requests

BASE = "https://api.schwabapi.com/marketdata/v1/pricehistory"
HEADERS = {"Authorization": f"Bearer {"C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.zjs4PL4ht_kEPZW23sEGGZndVWFpThwGAkDRAbXFufw%40"}"}

# Example A: last 5 trading days of 1-minute bars
params = dict(
    symbol="AAPL",
    periodType="day",      # day|month|year|ytd
    period=5,              # allowed values depend on periodType
    frequencyType="minute",# minute|daily|weekly|monthly (constrained by periodType)
    frequency=1,           # minute: 1,5,10,15,30; others: 1
    needExtendedHoursData="false",
    needPreviousClose="false",
)
r = requests.get(BASE, headers=HEADERS, params=params, timeout=30)
r.raise_for_status()
j = r.json()

print(j)