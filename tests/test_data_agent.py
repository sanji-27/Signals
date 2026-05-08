import pytest
import pandas as pd
from src.agents.data_agent import DataAgent
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_data_agent_on_candle():
    agent = DataAgent(token="fake_token")
    # Mock message for e:1003
    message = {
        "e": 1003,
        "pair": "EURUSD",
        "size": 300,
        "d": [{"t": 1625097600, "o": 1.1, "h": 1.2, "l": 1.0, "c": 1.15}]
    }
    await agent._on_candle(message)

    df = agent.get_latest_candles("EURUSD", size=300)
    assert not df.empty
    assert len(df) == 1
    assert df.iloc[0]['close'] == 1.15

@pytest.mark.asyncio
async def test_data_agent_fallback(monkeypatch):
    # Mock AlphaVantageClient
    mock_av = MagicMock()
    mock_av.get_candles = AsyncMock(return_value=pd.DataFrame(
        [{"open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15}],
        index=[pd.Timestamp.now()]
    ))

    agent = DataAgent(token="fake_token")
    agent.fallback = mock_av

    await agent._load_fallback("EURUSD")
    df = agent.get_latest_candles("EURUSD", size=300)
    assert not df.empty
    assert df.iloc[0]['close'] == 1.15
