import asyncio
import logging
import pandas as pd
from typing import Dict, List, Optional, Callable
from olymptrade_ws import OlympTradeClient
from config.config import Config

logger = logging.getLogger(__name__)

class DataAgent:
    def __init__(self, token: str):
        self.client = OlympTradeClient(access_token=token)
        self._raw_ticks: Dict[str, List[dict]] = {asset: [] for asset in Config.ASSETS + Config.OTC_ASSETS}
        self._raw_candles: Dict[str, List[dict]] = {}
        self.max_buffer_size = 1000
        self.on_trade_result: Optional[Callable[[str, str, float], None]] = None

        # Register callbacks
        self.client.register_callback(1, self._on_tick)
        self.client.register_callback(1003, self._on_candle)
        # Trade events: 26 is trade closed
        self.client.register_callback(26, self._on_trade_closed)

    async def start(self):
        """Start the OlympTrade client."""
        logger.info("Starting DataAgent...")
        await self.client.start()

        for asset in Config.ASSETS + Config.OTC_ASSETS:
            try:
                await self.client.market.subscribe_ticks(asset)
                for size in [60, 300, 900]:
                    await self.client.send_request(10, [{"pair": asset, "size": size, "solid": True}])
            except Exception as e:
                logger.error(f"Failed to subscribe to {asset}: {e}")

    async def stop(self):
        await self.client.stop()

    async def _on_tick(self, message: dict):
        ticks = message.get("d", [])
        for tick in ticks:
            pair = tick.get("p")
            if pair in self._raw_ticks:
                self._raw_ticks[pair].append(tick)
                if len(self._raw_ticks[pair]) > self.max_buffer_size:
                    self._raw_ticks[pair].pop(0)

    async def _on_candle(self, message: dict):
        candles = message.get("d", [])
        pair = message.get("pair") or (candles[0].get("p") if candles else None)
        size = message.get("size")
        if pair:
            key = f"{pair}_{size}" if size else pair
            if key not in self._raw_candles:
                self._raw_candles[key] = []
            self._raw_candles[key].extend(candles)
            if len(self._raw_candles[key]) > self.max_buffer_size:
                self._raw_candles[key] = self._raw_candles[key][-self.max_buffer_size:]

    async def _on_trade_closed(self, message: dict):
        """Handle trade closure and trigger updates."""
        trade_data = message.get("d", [])
        if not trade_data:
            return

        trade = trade_data[0]
        asset = trade.get("pair")
        pnl = trade.get("balance_change", 0.0)
        outcome = "WIN" if pnl > 0 else "LOSS"

        logger.info(f"Trade Closed: {asset}, Result: {outcome}, PnL: {pnl}")

        if self.on_trade_result:
            self.on_trade_result(asset, outcome, pnl)

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

    def get_latest_candles(self, pair: str, size: int = 300, limit: int = 100) -> pd.DataFrame:
        key = f"{pair}_{size}"
        candles = self._raw_candles.get(key, [])[-limit:]
        if not candles:
            # Try plain pair if size-specific not found
            candles = self._raw_candles.get(pair, [])[-limit:]

        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles)
        if 't' in df.columns:
            df['datetime'] = pd.to_datetime(df['t'], unit='s')
            df.set_index('datetime', inplace=True)
        return df
