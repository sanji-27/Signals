import asyncio
import logging
import pandas as pd
from typing import Dict, List, Optional
from olymptrade_ws import OlympTradeClient
from config.config import Config

logger = logging.getLogger(__name__)

class DataAgent:
    def __init__(self, token: str):
        self.client = OlympTradeClient(access_token=token)
        # Store data as Dict of lists of dicts, to be converted to DataFrame when needed
        self._raw_ticks: Dict[str, List[dict]] = {asset: [] for asset in Config.ASSETS + Config.OTC_ASSETS}
        self._raw_candles: Dict[str, List[dict]] = {asset: [] for asset in Config.ASSETS + Config.OTC_ASSETS}
        self.max_buffer_size = 1000  # Keep last 1000 data points per asset

        # Register callbacks
        self.client.register_callback(1, self._on_tick)
        self.client.register_callback(1003, self._on_candle)

    async def start(self):
        """Start the OlympTrade client."""
        logger.info("Starting DataAgent...")
        await self.client.start()

        # Subscribe to assets
        for asset in Config.ASSETS + Config.OTC_ASSETS:
            try:
                await self.client.market.subscribe_ticks(asset)
                logger.debug(f"Subscribed to {asset} ticks")
            except Exception as e:
                logger.error(f"Failed to subscribe to {asset}: {e}")

    async def stop(self):
        """Stop the OlympTrade client."""
        logger.info("Stopping DataAgent...")
        await self.client.stop()

    async def _on_tick(self, message: dict):
        """Handle incoming tick data."""
        ticks = message.get("d", [])
        for tick in ticks:
            pair = tick.get("p")
            if pair in self._raw_ticks:
                self._raw_ticks[pair].append(tick)
                # Maintain buffer size
                if len(self._raw_ticks[pair]) > self.max_buffer_size:
                    self._raw_ticks[pair].pop(0)

    async def _on_candle(self, message: dict):
        """Handle incoming candle data."""
        candles = message.get("d", [])
        pair = message.get("pair") # Assuming pair is in message or passed somehow
        if not pair and candles:
             # Try to infer pair from first candle if available
             pair = candles[0].get("p")

        if pair and pair in self._raw_candles:
            self._raw_candles[pair].extend(candles)
            # Maintain buffer size
            if len(self._raw_candles[pair]) > self.max_buffer_size:
                self._raw_candles[pair] = self._raw_candles[pair][-self.max_buffer_size:]

    async def get_historical_candles(self, pair: str, size: int, count: int) -> pd.DataFrame:
        """Fetch historical candles and return as DataFrame."""
        candles = await self.client.market.get_candles(pair, size, count)
        if candles:
            df = pd.DataFrame(candles)
            if 't' in df.columns:
                df['datetime'] = pd.to_datetime(df['t'], unit='s')
                df.set_index('datetime', inplace=True)
            return df
        return pd.DataFrame()

    def get_latest_ticks(self, pair: str, limit: int = 100) -> pd.DataFrame:
        """Return the latest available ticks for a pair."""
        ticks = self._raw_ticks.get(pair, [])[-limit:]
        if not ticks:
            return pd.DataFrame()
        df = pd.DataFrame(ticks)
        if 't' in df.columns:
            df['datetime'] = pd.to_datetime(df['t'], unit='s')
            df.set_index('datetime', inplace=True)
        return df

    def get_latest_candles(self, pair: str, limit: int = 100) -> pd.DataFrame:
        """Return the latest available candles for a pair."""
        candles = self._raw_candles.get(pair, [])[-limit:]
        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles)
        if 't' in df.columns:
            df['datetime'] = pd.to_datetime(df['t'], unit='s')
            df.set_index('datetime', inplace=True)
        return df
