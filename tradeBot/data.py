import requests
import pandas as pd
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt 


ET = ZoneInfo("America/New_York")

def get_candles(
    data_access_token: str,
    symbol: str,
    period_type: str,
    frequency_type: str,
    period: int = 1,
    frequency: int = 1,
    need_extended_hours_data: bool = False,
) -> pd.DataFrame:
    """Fetch Schwab candles → DataFrame with ET DatetimeIndex and numeric OHLCV."""
    url = "https://api.schwabapi.com/marketdata/v1/pricehistory"
    headers = {"Authorization": f"Bearer {data_access_token}"}
    params = {
        "symbol": symbol,
        "periodType": period_type,
        "period": period,
        "frequencyType": frequency_type,
        "frequency": frequency,
        "needExtendedHoursData": str(need_extended_hours_data).lower(),
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "candles" not in data:
        raise ValueError(f"Unexpected response (no 'candles'): {data}")

    candles = data["candles"]
    if not candles:
        # Return an empty, well-typed frame rather than crashing later
        cols = ["open", "high", "low", "close", "volume"]
        return pd.DataFrame(columns=cols, index=pd.DatetimeIndex([], tz=ET))

    df = pd.DataFrame(candles)
    # Ensure numeric types (the API is usually numeric, but be defensive)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # datetime is epoch ms UTC → tz-aware
    df["datetime"] = pd.to_datetime(df["datetime"], unit="ms", utc=True)
    df.set_index("datetime", inplace=True)

    # Convert to ET for your downstream logic
    df = df.tz_convert(ET)
    return df.sort_index()


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