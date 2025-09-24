import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt 


def get_candles(
    access_token: str, 
    symbol: str, period_type: str, 
    frequency_type: str, 
    period: int = 1, 
    frequency: int = 1, 
    need_extended_hours_data: bool = False) -> pd.DataFrame:

    """
    Ping the Charles Schwab API for historical candles
    and return a normalized DataFrame with datetime index.
    
    Returns a DataFrame with columns:
    ['open', 'high', 'low', 'close', 'volume']
    indexed by UTC datetime.
    """

    url = "https://api.schwabapi.com/marketdata/v1/pricehistory"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "symbol": symbol,
        "periodType": period_type,     # must be month or year if you want daily bars
        "period": period,               # 1 month window
        "frequencyType": frequency_type,  # daily bars
        "frequency": frequency,            # every 1 day
        "needExtendedHoursData": str(need_extended_hours_data).lower()
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    
    resp_json = resp.json()

    #convert candles to dataframe
    df = pd.DataFrame(resp_json["candles"])

    #convers datetime (ms since epoch/1970) -> readable timetamp
    df["datetime"] = pd.to_datetime(df["datetime"], unit="ms", utc=True)

    #Make datetime the index
    df.set_index("datetime", inplace=True)

    return df
