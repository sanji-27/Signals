import pandas as pd
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalystAgent:
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute extensive features using pandas_ta."""
        if df.empty or len(df) < 50:
            return df

        # Trend
        df.ta.ema(length=9, append=True)
        df.ta.ema(length=21, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=100, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.supertrend(length=7, multiplier=3, append=True)
        df.ta.ichimoku(append=True)

        # Momentum
        df.ta.rsi(length=14, append=True)
        df.ta.rsi(length=7, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.stoch(length=14, k=3, d=3, append=True)
        df.ta.willr(length=14, append=True)
        df.ta.cci(length=20, append=True)
        df.ta.uo(append=True)

        # Volatility
        df.ta.bbands(length=20, std=2.0, append=True)
        df.ta.atr(length=14, append=True)
        df.ta.kc(length=20, scalar=2, append=True)
        df.ta.donchian(lower_length=20, upper_length=20, append=True)

        # Volume (proxies if volume missing)
        if 'volume' in df.columns:
            df.ta.obv(append=True)
            df.ta.mfi(length=14, append=True)
            df.ta.pvt(append=True)
            if isinstance(df.index, pd.DatetimeIndex):
                df.ta.vwap(append=True)

        # Support/Resistance
        df['support'] = df['low'].rolling(window=20).min()
        df['resistance'] = df['high'].rolling(window=20).max()

        return df

    def analyze_trend(self, df: pd.DataFrame) -> str:
        if df.empty or 'EMA_50' not in df.columns or 'EMA_200' not in df.columns:
            return "unknown"

        price = df['close'].iloc[-1]
        ema_50 = df['EMA_50'].iloc[-1]
        ema_200 = df['EMA_200'].iloc[-1]

        if price > ema_50 > ema_200:
            return "trending_up"
        elif price < ema_50 < ema_200:
            return "trending_down"
        else:
            return "ranging"
