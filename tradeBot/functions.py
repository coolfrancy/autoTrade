import pandas as pd


def atr(df, period: int = 14) -> pd.Series:
    """Classic Wilder ATR."""
    h, l, c = df['high'], df['low'], df['close']
    prev_c = c.shift(1)
    tr = pd.concat([
        (h - l),
        (h - prev_c).abs(),
        (l - prev_c).abs()
    ], axis=1).max(axis=1)
    # Wilder smoothing: EMA with alpha = 1/period approximates Wilder
    return tr.ewm(alpha=1/period, adjust=False).mean()

def daily_percent_change(df) -> pd.Series:
    """
    Percent change of **daily close**.
    If df is intraday, resample to daily close and forward-fill back to intraday index
    so it behaves like ThinkScript's close(period=AggregationPeriod.DAY).
    """
    if df.index.inferred_type in ("datetime64", "datetime64tz"):
        # build a daily close series on business days
        daily_close = df['close'].resample('1D').last()
        # limit to business days only if you prefer:
        # daily_close = df['close'].asfreq('B')  # optional
        pct_daily = daily_close.pct_change() * 100.0
        # align to original index by forward-filling yesterday’s computed value
        pct_on_intraday_index = pct_daily.reindex(df.index, method='ffill')
        return pct_on_intraday_index
    else:
        # if df is already daily, just use pct_change on close
        return df['close'].pct_change() * 100.0

# --- Core translation -------------------------------------------------------

def hot_stock_swing_mask(df, percent_change_threshold: float = 5.0) -> pd.Series:
    """
    ThinkScript:
      def hotstockswing =
        PercentChg(price=close(period=DAY))[1] > PercentChange AND
        PercentChg(price=close(period=DAY))[2] > PercentChange AND
        PercentChg(price=close(period=DAY))     > PercentChange;
    """
    pct = daily_percent_change(df)  # on intraday this is the daily change aligned to each bar
    cond = (pct.shift(1) > percent_change_threshold) & \
           (pct.shift(2) > percent_change_threshold) & \
           (pct > percent_change_threshold)
    return cond.fillna(False)