import requests
import pandas as pd
import matplotlib.pyplot as plt 


def get_candles(
    DATA_ACCESS_TOKEN: str, 
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
        "Authorization": f"Bearer {DATA_ACCESS_TOKEN}"
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

def plot(df, show_strategy: bool = False, filename: str = "chart.png"):
    """
    Plot close price and optionally overlay strategy buy/sell signals.
    Expects df to have a 'close' column, and if show_strategy=True,
    also a 'strategy' column with values like 'buy', 'sell', or None.
    """
    plt.figure(figsize=(10, 5))

    # Always plot close price
    plt.plot(df.index, df["close"], label="Close", color="blue")

    if show_strategy and "strategy" in df.columns:
        # Plot buy signals
        buys = df[df["strategy"] == "buy"]
        plt.scatter(buys.index, buys["close"], marker="^", color="green", label="Buy", s=100)

        # Plot sell signals
        sells = df[df["strategy"] == "sell"]
        plt.scatter(sells.index, sells["close"], marker="v", color="red", label="Sell", s=100)

    plt.legend()
    plt.title("Strategy Chart")
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    get_candles()