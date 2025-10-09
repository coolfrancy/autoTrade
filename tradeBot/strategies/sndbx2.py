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

def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).mean()

# --- ThinkScript time helpers replicated on ET clock ---
def seconds_from_time(idx_utc: pd.DatetimeIndex, hhmm: int) -> pd.Series:
    # positive after the moment of hh:mm, negative before; 0 exactly at hh:mm
    et = idx_utc.tz_convert(ET)
    hh, mm = divmod(hhmm, 100)
    target = et.normalize() + pd.to_timedelta(hh, "h") + pd.to_timedelta(mm, "m")
    return (et - target).total_seconds()

def seconds_till_time(idx_utc: pd.DatetimeIndex, hhmm: int) -> pd.Series:
    et = idx_utc.tz_convert(ET)
    hh, mm = divmod(hhmm, 100)
    target = et.normalize() + pd.to_timedelta(hh, "h") + pd.to_timedelta(mm, "m")
    return (target - et).total_seconds()

def translate_strategy(df: pd.DataFrame) -> pd.DataFrame:
    if df.index.tzinfo is None:
        raise ValueError("Index must be timezone-aware (UTC).")

    out = df.copy()

    # Inputs/constants from your script
    marketopen   = 930
    marketclose  = 1557
    pt = 2.0
    stop_loss_percentage = 0.9
    PositionSize = 300
    PositionSize_half = 150

    # Plots/indicators
    out["SMA_200"] = sma(out["close"], 200)
    out["ATR_14"]  = atr_wilder(out, 14)
    out["RSI_14"]  = rsi_wilder(out["close"], 14)

    # Time conditions (ThinkScript semantics)
    begin = seconds_from_time(out.index, marketopen)         # > 0 after 09:30
    end   = seconds_till_time(out.index, marketclose)        # > 0 before 15:57

    eod = end < 121                                          # last 121 seconds before 15:57
    tradingday = (begin > 0) & (end > 0)                     # between 09:30 and 15:57

    powerOpen = (seconds_from_time(out.index, 930) >= 0) & (seconds_till_time(out.index, 1000) > 0)   # [09:30,10:00)
    powerEnd  = (seconds_from_time(out.index, 1500) >= 0) & (seconds_till_time(out.index, 1530) > 0)  # [15:00,15:30)

    # Buying power threshold reused in labels
    buyingpower = 3000 / out["close"]

    # Stop based on ATR
    # stop_loss_distance = ATR * stop_loss_percentage
    # stop_loss_price = EntryPrice - stop_loss_distance
    # (EntryPrice handled in the walk-forward loop)

    # Entrance rules
    is_bullish = out["close"] > out["close"].shift(1)
    meets_volume_requirement = out["volume"] > (3000 / out["close"]) * 100
    meets_rsi_requirement = (out["RSI_14"] - out["RSI_14"].shift(1)) > 10
    should_enter = (is_bullish & meets_volume_requirement & meets_rsi_requirement) & (powerOpen | powerEnd)

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

    # Optional: columns that mimic your labels’ underlying values (for debugging or UI)
    out["label_volume_x100_ok"] = out["volume"] > (buyingpower / out["close"]) * 100
    out["label_rsi_diff"] = (out["RSI_14"] - out["RSI_14"].shift(1)).round(1)

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