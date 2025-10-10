import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from data import get_candles, plot
from dotenv import load_dotenv
import pandas_ta as ta
import pandas as pd


from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# --- Indicators ---
def atr_wilder(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def translate_strategy(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    pt = 2.0
    stop_loss_percentage = 0.9

    # Plots/indicators
    out["ATR_14"]  = atr_wilder(out, 14)
    out["RSI_14"]  = rsi_wilder(out["close"], 14)

    # Stop based on ATR
    # stop_loss_distance = ATR * stop_loss_percentage
    # stop_loss_price = EntryPrice - stop_loss_distance
    # (EntryPrice handled in the walk-forward loop)

    # Entrance rules
    is_bullish = out["close"] > out["close"].shift(1)
    meets_volume_requirement = out["volume"] > (3000 / out["close"]) * 100
    meets_rsi_requirement = (out["RSI_14"] - out["RSI_14"].shift(1)) > 10
    should_enter = (is_bullish & meets_volume_requirement & meets_rsi_requirement)

#///
    # Edit rules (not used in final exits per your code, but computed for parity)
    price_diff = out["high"] - np.nan  # depends on EntryPrice; set in loop for exact value per bar
    meets_close_requirement = out["close"] < out["low"].shift(1)
    meets_atr_requirement = out["high"].shift(0) - np.nan  # evaluated in-loop as well

    # Outputs mirroring plots/labels
    out["Highatr"] = np.nan
    out["Lowatr"]  = np.nan
    out["touches_Highatr"] = False
    out["strategy"] = None

    # Walk-forward to honor EntryPrice(), Highatr/Lowatr, exits, and single-position logic
    in_pos = False
    entry = np.nan

    for i in range(len(out)):
        if not in_pos:
            if bool(should_enter.iat[i] and tradingday.iat[i]):
                in_pos = True
                entry = out["close"].iat[i]
                # Compute current Highatr/Lowatr after entry (for plotting parity)
                highatr_i = entry + out["ATR_14"].iat[i] * pt
                lowatr_i  = entry - out["ATR_14"].iat[i] * stop_loss_percentage
                out.iat[i, out.columns.get_loc("Highatr")] = highatr_i
                out.iat[i, out.columns.get_loc("Lowatr")]  = lowatr_i
                out.iat[i, out.columns.get_loc("strategy")] = "buy"
        else:
            # Current thresholds
            highatr_i = entry + out["ATR_14"].iat[i] * pt
            lowatr_i  = entry - out["ATR_14"].iat[i] * stop_loss_percentage
            out.iat[i, out.columns.get_loc("Highatr")] = highatr_i
            out.iat[i, out.columns.get_loc("Lowatr")]  = lowatr_i

            # Exit rules: eod OR low < stop_loss_price OR high >= Highatr
            should_exit = (out["low"].iat[i] < lowatr_i) | (out["high"].iat[i] >= highatr_i) | bool(eod.iat[i])

            # touches_Highatr = high >= Highatr and high[1] < Highatr(previous)
            if i > 0:
                touched_now = out["high"].iat[i] >= highatr_i
                touched_prev = out["high"].iat[i-1] < (entry + out["ATR_14"].iat[i-1] * pt)
                out.iat[i, out.columns.get_loc("touches_Highatr")] = bool(touched_now and touched_prev)

            if should_exit:
                in_pos = False
                out.iat[i, out.columns.get_loc("strategy")] = "sell"
                entry = np.nan

    return out

if __name__ == "__main__":
    load_dotenv()
    DATA_ACCESS_TOKEN = os.getenv("DATA_ACCESS_TOKEN")

    #The type of data that i want
    symbol = "SPY"
    period_type = "day"
    frequency_type = "minute"


    df = get_candles(DATA_ACCESS_TOKEN, symbol, period_type, frequency_type, period=10, frequency=5)
    dfStrat = translate_strategy(df)
    print(dfStrat[dfStrat["strategy"] == "buy"])

    plot(dfStrat, True)