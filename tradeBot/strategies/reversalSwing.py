import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from data import get_candles, plot
from dotenv import load_dotenv
import pandas_ta as ta
import pandas as pd
import numpy as np


load_dotenv()

def strategy_sma_rsi(df):
    """
    ThinkScript:
      SMA = simplemovingavg(length=200)
      FMA = simplemovingavg(length=400)
      BUY  when RSI() < 40 and low > SMA      (filled at close)
      SELL when RSI() > 55                    (filled at close)
           or low <= FMA                      (filled at close)

    Returns df with columns: SMA_200, FMA_400, RSI_14, strategy ('buy'/'sell'/None).
    Long-only, single-position, fills at close.
    """
    out = df.copy()

    # Indicators
    out["SMA_200"] = ta.sma(out["close"], length=200)
    out["FMA_400"] = ta.sma(out["close"], length=400)
    out["RSI_14"]  = ta.rsi(out["close"], length=14)

    # Entry/exit conditions (vector masks)
    entry_mask = (out["RSI_14"] < 40) & (out["low"] > out["SMA_200"])
    exit_mask  = (out["RSI_14"] > 55) | (out["low"] <= out["FMA_400"])

    # Walk forward to enforce single-position logic
    out["strategy"] = None
    in_pos = False
    for i in range(len(out)):
        if not in_pos and entry_mask.iat[i]:
            out.iat[i, out.columns.get_loc("strategy")] = "buy"
            in_pos = True
        elif in_pos and exit_mask.iat[i]:
            out.iat[i, out.columns.get_loc("strategy")] = "sell"
            in_pos = False

    return out

if __name__ == "__main__":
    DATA_ACCESS_TOKEN = os.getenv("DATA_ACCESS_TOKEN")

    #The type of data that i want
    symbol = "SPY"
    period_type = "year"
    frequency_type = "daily"


    df = get_candles(DATA_ACCESS_TOKEN, symbol, period_type, frequency_type, period=10)
    dfStrat = strategy_sma_rsi(df)
    plot(dfStrat, True)