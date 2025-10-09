import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from data import get_candles, plot
from dotenv import load_dotenv
import pandas_ta as ta
import pandas as pd


load_dotenv()

def above_200_sma(df):
    # Calculate the 200-period SMA
    sma = ta.sma(df["close"], length=200)

    # Yesterday's close below SMA AND today's close above SMA → BUY
    df["strategy"] = None  # initialize
    df.loc[(df["close"].shift(1) < sma.shift(1)) & (df["close"] > sma), "strategy"] = "buy"
    df.loc[(df["close"].shift(1) > sma.shift(1)) & (df["close"] < sma), "strategy"] = "sell"

    return df        


if __name__ == "__main__":
    DATA_ACCESS_TOKEN = os.getenv("DATA_ACCESS_TOKEN")

    #The type of data that i want
    symbol = "SPY"
    period_type = "year"
    frequency_type = "daily"


    df = get_candles(DATA_ACCESS_TOKEN, symbol, period_type, frequency_type, period=10)
    dfStrat = above_200_sma(df)
    print(dfStrat)
    plot(dfStrat, True)