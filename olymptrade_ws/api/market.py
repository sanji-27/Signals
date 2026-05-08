# api/market.py
import logging
import time
from typing import TYPE_CHECKING, Dict, Any, Optional, List, Union
from datetime import datetime, timezone

import olymptrade_ws.olympconfig.parameters as settings
from olymptrade_ws.core.protocol import get_current_timestamp_ms

if TYPE_CHECKING:
    from olymptrade_ws.core.client import OlympTradeClient

logger = logging.getLogger(__name__)

class MarketAPI:
    def __init__(self, client: 'OlympTradeClient'):
        self._client = client

    async def subscribe_ticks(self, pair: str) -> None:
        """Subscribes to live price ticks (Event 1) for a given asset pair."""
        logger.info(f"Subscribing to ticks for {pair}...")
        try:
            await self._client.send_request(12, [{"pair": pair}], requires_response=True)
            await self._client.send_request(280, [{"pair": pair}], requires_response=True)
            logger.info(f"Successfully sent tick subscription requests for {pair}.")
        except Exception as e:
            logger.error(f"Failed to subscribe to ticks for {pair}: {e}")
            raise

    async def subscribe_candles(self, pair: str, size: int) -> None:
        """Subscribes to live candles (Event 1003) for a given asset pair."""
        logger.info(f"Subscribing to candles for {pair} (size: {size})...")
        try:
            # Event 11 seems to be for candle subscription in some versions
            await self._client.send_request(11, [{"pair": pair, "size": size}], requires_response=True)
            logger.info(f"Successfully sent candle subscription request for {pair}.")
        except Exception as e:
            logger.error(f"Failed to subscribe to candles for {pair}: {e}")
            raise

    async def get_candles(self, pair: str, size: int, count: int, end_time: Optional[Union[datetime, int]] = None) -> Optional[List[Dict[str, Any]]]:
        if end_time is None:
            to_ts = int(time.time())
        elif isinstance(end_time, datetime):
            if end_time.tzinfo is None:
                 end_time = end_time.replace(tzinfo=timezone.utc)
            to_ts = int(end_time.timestamp())
        else:
            to_ts = int(end_time)

        data = [{"pair": pair, "size": size, "to": to_ts, "solid": True}]
        try:
            response = await self._client.send_request(10, data, requires_response=True)
            if response and response.get("e") == 1003:
                 return response.get("d")
            return None
        except Exception as e:
            logger.error(f"Failed to get candles for {pair}: {e}")
            return None
