import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os

# --- Indicators (ATR via Wilder smoothing) ---
def atr_wilder(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    prev_c = c.shift(1)
    tr = pd.concat([(h - l), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

# --- Time window helpers (on ET) ---
ET = ZoneInfo("America/New_York")

def in_intraday_window(idx_utc: pd.DatetimeIndex,
                       start_hm=(9,30), end_hm=(15,57)) -> pd.Series:
    et = idx_utc.tz_convert(ET)
    after_open  = (et.hour > start_hm[0]) | ((et.hour == start_hm[0]) & (et.minute >= start_hm[1]))
    before_close= (et.hour < end_hm[0])   | ((et.hour == end_hm[0])   & (et.minute <  end_hm[1]))
    return after_open & before_close

def between(idx_utc: pd.DatetimeIndex, start_hm, end_hm) -> pd.Series:
    et = idx_utc.tz_convert(ET)
    ge_start = (et.hour > start_hm[0]) | ((et.hour == start_hm[0]) & (et.minute >= start_hm[1]))
    lt_end   = (et.hour < end_hm[0])   | ((et.hour == end_hm[0])   & (et.minute <  end_hm[1]))
    return ge_start & lt_end

def last_seconds_before(idx_utc: pd.DatetimeIndex, close_hm=(15,57), seconds=121) -> pd.Series:
    et = idx_utc.tz_convert(ET)
    # compute seconds until close_hm within the same day; negative/large values → False
    close_ts = et.normalize() + pd.to_timedelta(close_hm[0], "h") + pd.to_timedelta(close_hm[1], "m")
    secs_left = (close_ts - et).total_seconds()
    return (secs_left < seconds) & (secs_left >= 0)

# --- Main strategy translation ---
def strategy_power_open_end(df: pd.DataFrame) -> pd.DataFrame:
    """
    ThinkScript (paraphrased):
      marketopen=0930, marketclose=1557
      powerOpen: 09:30–10:00; powerEnd: 15:00–15:30
      tradingday: between 09:30 and 15:57
      ATR = Wilder ATR(14)
      stop_loss_distance = ATR * 0.9
      stop_loss_price = EntryPrice - stop_loss_distance
      Highatr = EntryPrice + ATR * pt   (pt=2)
      Entry if: close>close[1] and volume > (3000/close)*100 and (RSI() - RSI()[1]) > 10 and (powerOpen or powerEnd)
      Exit  if: eod (SecondsTillTime(15:57) < 121) or low < stop_loss_price or high >= Highatr
      Orders: BUY_TO_OPEN on entry; SELL_TO_CLOSE on exit; single position
    """
    out = df.copy()

    # Preconditions
    if out.index.tzinfo is None:
        raise ValueError("DataFrame index must be timezone-aware (UTC recommended).")

    # Time masks
    tradingday = in_intraday_window(out.index, (9,30), (15,57))
    power_open = between(out.index, (9,30), (10,0))
    power_end  = between(out.index, (15,0), (15,30))
    eod        = last_seconds_before(out.index, (15,57), seconds=121)

    # Indicators
    atr = atr_wilder(out, period=14)
    # Simple RSI 14 (Wilder). If you have pandas_ta, replace with ta.rsi(close,14).
    delta = out["close"].diff()
    gain  = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))

    # Entry components
    is_bullish = out["close"] > out["close"].shift(1)
    buying_power_shares_threshold = (3000 / out["close"]) * 100
    meets_volume = out["volume"] > buying_power_shares_threshold
    meets_rsi    = (rsi - rsi.shift(1)) > 10
    should_enter = (is_bullish & meets_volume & meets_rsi) & (power_open | power_end) & tradingday

    # Params
    pt = 2.0
    stop_loss_pct = 0.9

    # Walk-forward state
    out["strategy"] = None
    in_pos = False
    entry = np.nan

    for i in range(len(out)):
        if not in_pos:
            if bool(should_enter.iat[i]):
                in_pos = True
                entry = out["close"].iat[i]
                out.iat[i, out.columns.get_loc("strategy")] = "buy"
        else:
            highatr = entry + atr.iat[i] * pt
            stop_loss_price = entry - atr.iat[i] * stop_loss_pct

            exit_now = bool(eod.iat[i]) or (out["low"].iat[i] < stop_loss_price) or (out["high"].iat[i] >= highatr)
            if exit_now:
                out.iat[i, out.columns.get_loc("strategy")] = "sell"
                in_pos = False
                entry = np.nan

    return out

if __name__ == "__main__":
    strategy_power_open_end()

    DATA_ACCESS_TOKEN = os.getenv("DATA_ACCESS_TOKEN")

    #The type of data that i want
    symbol = "SPY"
    period_type = "year"
    frequency_type = "daily"


    df = get_candles(DATA_ACCESS_TOKEN, symbol, period_type, frequency_type, period=10)
    dfStrat = above_200_sma(df)
    plot(dfStrat, True)