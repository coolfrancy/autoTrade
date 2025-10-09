import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from data import get_candles, plot

def sndbx2(df):
    stop_loss_percentage = 0.9


def atr_tos(df, length: int = 14) -> pd.Series:
    """
    Thinkorswim-accurate ATR (Wilder) with the same seeding/NaN behavior.

    Requires columns: 'high', 'low', 'close'
    Returns a pd.Series named 'ATR' with NaN for the first length-1 rows.
    """
    high = df['high'].astype(float)
    low = df['low'].astype(float)
    close = df['close'].astype(float)
    prev_close = close.shift(1)

    # True Range per TOS
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    n = length
    atr = pd.Series(np.nan, index=df.index, name='ATR')

    if len(tr) < n:
        return atr  # not enough data to seed

    # Seed at bar n-1: simple average of the first n TR values
    seed = tr.iloc[:n].mean()
    atr.iloc[n-1] = seed

    # Wilder recursive smoothing from bar n onward
    for i in range(n, len(tr)):
        atr.iloc[i] = atr.iloc[i-1] + (tr.iloc[i] - atr.iloc[i-1]) / n

    return atr





if __name__ == "__main__":
    load_dotenv()
    DATA_ACCESS_TOKEN = os.getenv("DATA_ACCESS_TOKEN")

    #The type of data that i want
    symbol = "AAPL"
    period_type = "day"
    frequency_type = "minute"


    df = get_candles(DATA_ACCESS_TOKEN, symbol, period_type, frequency_type, period=10, need_extended_hours_data=True)
    #print(atr_tos(df).tail())
    print(df.tail())