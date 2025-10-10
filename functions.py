import pandas as pd
import numpy as np


# --- Indicators ---
def atr_wilder(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    to closely match thinkorswim wilder function, must get data for 3x the period length
    """ 

    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def rsi_wilder(close: pd.Series, period: int = 2) -> pd.Series:
    """
    to closely match thinkorswim wilder function, must get data for 3x the period length
    """ 

    delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
            loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
                rs = gain / loss.replace(0, np.nan)
                    return 100 - (100 / (1 + rs))
                    
def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).mean()

if __name__ == "__main__":
    atr_wilder()