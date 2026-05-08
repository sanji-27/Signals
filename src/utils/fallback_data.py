import requests
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"

    def get_candles(self, symbol: str, interval: str = "5min") -> pd.DataFrame:
        """Fetch historical candles as fallback."""
        if not self.api_key:
            logger.warning("Alpha Vantage API Key missing. Fallback unavailable.")
            return pd.DataFrame()

        # Map Olymp Trade symbols to Forex symbols if needed
        # Simple mapping for major pairs
        av_symbol = symbol.replace("/", "")
        if "_OTC" in av_symbol:
            av_symbol = av_symbol.replace("_OTC", "")

        params = {
            "function": "FX_INTRADAY",
            "from_symbol": av_symbol[:3],
            "to_symbol": av_symbol[3:],
            "interval": interval,
            "apikey": self.api_key,
            "outputsize": "compact"
        }

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()

            key = f"Time Series FX ({interval})"
            if key not in data:
                logger.error(f"Alpha Vantage error: {data.get('Note', 'Unknown error')}")
                return pd.DataFrame()

            df = pd.DataFrame.from_dict(data[key], orient='index')
            df.columns = ['open', 'high', 'low', 'close']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            return df
        except Exception as e:
            logger.error(f"Failed to fetch fallback data: {e}")
            return pd.DataFrame()
