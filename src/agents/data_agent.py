import asyncio
import logging
import pandas as pd
from typing import Dict, List, Optional, Callable
from olymptrade_ws import OlympTradeClient
from config.config import Config
from src.utils.fallback_data import AlphaVantageClient

logger = logging.getLogger(__name__)

class DataAgent:
    """Handles real-time WebSocket data with fallback to Alpha Vantage."""
    def __init__(self, token: str):
        self.client = OlympTradeClient(access_token=token)
        self.fallback = AlphaVantageClient()
        self._raw_candles: Dict[str, List[dict]] = {}
        self.max_buffer_size = 1000
        self.on_trade_result: Optional[Callable[[str, str, float], None]] = None

        # Register callbacks
        self.client.register_callback(1003, self._on_candle)
        self.client.register_callback(26, self._on_trade_closed)

    async def start(self):
        logger.info("Starting DataAgent...")
        await self.client.start()

        for asset in Config.ASSETS + Config.OTC_ASSETS:
            try:
                await self.client.market.subscribe_candles(asset, size=60)
                # Request initial historical data
                await self.refresh_candles(asset)
            except Exception as e:
                logger.error(f"Failed to subscribe to {asset}: {e}")

    async def refresh_candles(self, asset: Optional[str] = None):
        """Request data from WS or Fallback."""
        assets = [asset] if asset else (Config.ASSETS + Config.OTC_ASSETS)

        for a in assets:
            if self.client.connection.is_connected:
                try:
                    await self.client.send_request(10, [{"pair": a, "size": 300, "solid": True}]) # 5m
                    await self.client.send_request(10, [{"pair": a, "size": 900, "solid": True}]) # 15m
                except Exception as e:
                    logger.warning(f"WS Candle request failed for {a}: {e}")
                    self._load_fallback(a)
            else:
                self._load_fallback(a)

    def _load_fallback(self, asset: str):
        """Fetch data from Alpha Vantage as fallback."""
        logger.info(f"Using fallback data for {asset}")
        df_5m = self.fallback.get_candles(asset, "5min")
        if not df_5m.empty:
            self._update_internal_buffer(asset, 300, df_5m)

        df_15m = self.fallback.get_candles(asset, "15min")
        if not df_15m.empty:
            self._update_internal_buffer(asset, 900, df_15m)

    def _update_internal_buffer(self, asset: str, size: int, df: pd.DataFrame):
        key = f"{asset}_{size}"
        candles = []
        for ts, row in df.iterrows():
            candles.append({
                "t": int(ts.timestamp()),
                "o": row['open'],
                "h": row['high'],
                "l": row['low'],
                "c": row['close']
            })
        self._raw_candles[key] = candles

    async def stop(self):
        await self.client.stop()

    async def _on_candle(self, message: dict):
        candles = message.get("d", [])
        pair = message.get("pair")
        size = message.get("size")
        if pair:
            key = f"{pair}_{size}"
            if key not in self._raw_candles:
                self._raw_candles[key] = []

            self._raw_candles[key].extend(candles)
            df_temp = pd.DataFrame(self._raw_candles[key])
            if not df_temp.empty and 't' in df_temp.columns:
                df_temp = df_temp.drop_duplicates(subset=['t']).sort_values('t')
                self._raw_candles[key] = df_temp.tail(self.max_buffer_size).to_dict('records')

    async def _on_trade_closed(self, message: dict):
        trade_data = message.get("d", [])
        if not trade_data: return
        trade = trade_data[0]
        asset = trade.get("pair")
        pnl = trade.get("balance_change", 0.0)
        outcome = "WIN" if pnl > 0 else "LOSS"
        if self.on_trade_result:
            self.on_trade_result(asset, outcome, pnl)

    def get_latest_candles(self, pair: str, size: int = 300, limit: int = 100) -> pd.DataFrame:
        key = f"{pair}_{size}"
        candles = self._raw_candles.get(key, [])[-limit:]
        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles)
        if 't' in df.columns:
            # Rename columns to match technical analyst expectations
            df = df.rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close'})
            df['datetime'] = pd.to_datetime(df['t'], unit='s')
            df.set_index('datetime', inplace=True)
        return df
