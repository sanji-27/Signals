import logging
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MarketRegimeAgent:
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or len(df) < 20:
            return {"regime": "ranging"}

        adx_col = [col for col in df.columns if 'ADX_14' in col]
        if adx_col:
            adx = df[adx_col[0]].iloc[-1]
            regime = "trending" if adx > 25 else "ranging"
        else:
            regime = "ranging"

        return {"regime": regime}

class EnsembleOracleAgent:
    def __init__(self, analyst_agent, regime_agent, news_agent):
        self.analyst = analyst_agent
        self.regime_agent = regime_agent
        self.news_agent = news_agent

    def decide(self, df_5m: pd.DataFrame, df_15m: pd.DataFrame, asset: str) -> Dict[str, Any]:
        """Combine 5m entry with 15m trend confirmation."""
        if df_5m.empty or len(df_5m) < 50 or df_15m.empty or len(df_15m) < 50:
            return {"action": "wait", "confidence": 0.0}

        regime = self.regime_agent.analyze(df_5m)['regime']
        news_info = self.news_agent.get_sentiment()
        trend_15m = self.analyst.analyze_trend(df_15m)
        trend_5m = self.analyst.analyze_trend(df_5m)

        confidence = 0.0
        reasoning = []

        # 1. Multi-Timeframe Alignment (CRITICAL)
        if trend_15m == trend_5m and trend_15m != "ranging":
            confidence += 0.4
            reasoning.append(f"MTF Alignment: {trend_15m}")
        else:
            reasoning.append("MTF Mismatch")

        # 2. Technical Confluence
        rsi_col = [col for col in df_5m.columns if 'RSI_14' in col]
        if rsi_col:
            rsi = df_5m[rsi_col[0]].iloc[-1]
            if regime == "ranging":
                if rsi < 30:
                    confidence += 0.3
                    reasoning.append("RSI Oversold")
                elif rsi > 70:
                    confidence += 0.3
                    reasoning.append("RSI Overbought")
            else:
                if trend_5m == "trending_up" and rsi < 45:
                    confidence += 0.3
                    reasoning.append("RSI Pullback in Uptrend")
                elif trend_5m == "trending_down" and rsi > 55:
                    confidence += 0.3
                    reasoning.append("RSI Pullback in Downtrend")

        bb_lower = [col for col in df_5m.columns if 'BBL' in col]
        bb_upper = [col for col in df_5m.columns if 'BBU' in col]
        if bb_lower and bb_upper:
            close = df_5m['close'].iloc[-1]
            if close < df_5m[bb_lower[0]].iloc[-1]:
                confidence += 0.25
                reasoning.append("Price at Lower BB")
            elif close > df_5m[bb_upper[0]].iloc[-1]:
                confidence += 0.25
                reasoning.append("Price at Upper BB")

        macd_h_col = [col for col in df_5m.columns if 'MACDh' in col]
        if macd_h_col:
            hist = df_5m[macd_h_col[0]].iloc[-1]
            prev_hist = df_5m[macd_h_col[0]].iloc[-2]
            if hist > 0 and prev_hist <= 0:
                confidence += 0.15
                reasoning.append("MACD Bullish Cross")
            elif hist < 0 and prev_hist >= 0:
                confidence += 0.15
                reasoning.append("MACD Bearish Cross")

        # 3. News Filter
        if news_info['impact'] == "high":
            confidence -= 0.3
            reasoning.append("High Impact News Alert!")

        # Final Decision
        action = "wait"
        if confidence >= 0.95:
             if trend_5m == "trending_up" or (regime == "ranging" and df_5m['close'].iloc[-1] < df_5m[bb_lower[0]].iloc[-1]):
                 action = "CALL"
             else:
                 action = "PUT"

        return {
            "asset": asset,
            "action": action,
            "confidence": min(confidence, 1.0),
            "reasoning": "; ".join(reasoning),
            "regime": regime,
            "trend_confirmed": trend_15m == trend_5m
        }
