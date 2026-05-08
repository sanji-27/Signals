import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
import pandas as pd
from src.agents.data_agent import DataAgent

class TestDataAgent(unittest.IsolatedAsyncioTestCase):
    async def test_initialization(self):
        with unittest.mock.patch('src.agents.data_agent.OlympTradeClient') as MockClient:
            agent = DataAgent(token="fake_token")
            self.assertIsNotNone(agent.client)
            MockClient.return_value.register_callback.assert_called()

    async def test_tick_handling(self):
        with unittest.mock.patch('src.agents.data_agent.OlympTradeClient'):
            agent = DataAgent(token="fake_token")
            fake_tick = {"p": "EURUSD", "q": 1.0850, "t": 1715150000}
            await agent._on_tick({"d": [fake_tick]})

            df = agent.get_latest_ticks("EURUSD")
            self.assertFalse(df.empty)
            self.assertEqual(df.iloc[0]['q'], 1.0850)

    async def test_candle_handling(self):
        with unittest.mock.patch('src.agents.data_agent.OlympTradeClient'):
            agent = DataAgent(token="fake_token")
            fake_candle = {"p": "EURUSD", "o": 1.0850, "c": 1.0855, "t": 1715150000}
            await agent._on_candle({"d": [fake_candle], "pair": "EURUSD", "size": 300})

            df = agent.get_latest_candles("EURUSD", size=300)
            self.assertFalse(df.empty)
            self.assertEqual(df.iloc[0]['o'], 1.0850)

if __name__ == '__main__':
    unittest.main()
