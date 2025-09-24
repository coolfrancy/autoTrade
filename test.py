import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt 


ACCESS_TOKEN = "I0.b2F1dGgyLmNkYy5zY2h3YWIuY29t.6QrmpkezSmhHHcP7eAiS69ZQYpBjRXwvpKMOPmR7xfE@"

url = "https://api.schwabapi.com/marketdata/v1/pricehistory"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

params = {
    "symbol": "SPY",
    "periodType": "year",     # must be month or year if you want daily bars
    "period": 1,               # 1 month window
    "frequencyType": "daily",  # daily bars
    "frequency": 1,            # every 1 day
    "needExtendedHoursData": "false",
    "needPreviousClose": "false"
}


resp = requests.get(url, headers=headers, params=params, timeout=30)

print(resp.status_code)
resp_json = resp.json()

#convert candles to dataframe
df = pd.DataFrame(resp_json["candles"])

#convers datetime (ms since epoch/1970) -> readable timetamp
df["datetime"] = pd.to_datetime(df["datetime"], unit="ms", utc=True)

#Make datetime the index
df.set_index("datetime", inplace=True)

###insert strategy
#add a 200-period SMA on the close price 
df["SMA_200"] = ta.sma(df["close"], length=200)
####

print(df.tail())
print(len(df['open']))


#plot close price with sma
plt.figure(figsize=(10,5))
plt.plot(df.index, df["close"], label="close")
plt.plot(df.index, df["SMA_200"], label="SMA 20")
plt.legend()
plt.title("Apple with 20-period SMA")
plt.savefig("chart.png", dpi=300, bbox_inches="tight")