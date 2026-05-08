import unittest
import pandas as pd
import numpy as np
from src.agents.analyst_agent import TechnicalAnalystAgent

class TestTechnicalAnalystAgent(unittest.TestCase):
    def setUp(self):
        self.agent = TechnicalAnalystAgent()
        dates = pd.date_range('2024-01-01', periods=300, freq='5min')
        self.df = pd.DataFrame({
            'open': np.random.randn(300) + 100,
            'high': np.random.randn(300) + 101,
            'low': np.random.randn(300) + 99,
            'close': np.random.randn(300) + 100,
            'volume': np.random.randint(100, 1000, 300)
        }, index=dates)

    def test_compute_indicators(self):
        df_with_indicators = self.agent.compute_indicators(self.df.copy())
        self.assertIn('RSI_14', df_with_indicators.columns)
        self.assertIn('EMA_21', df_with_indicators.columns)
        self.assertIn('EMA_50', df_with_indicators.columns)
        self.assertIn('MACD_12_26_9', df_with_indicators.columns)
        self.assertIn('support', df_with_indicators.columns)

    def test_analyze_trend(self):
        df = self.df.copy()
        df['EMA_50'] = 105
        df['EMA_200'] = 100
        df['close'] = 110
        trend = self.agent.analyze_trend(df)
        self.assertEqual(trend, 'trending_up')

if __name__ == '__main__':
    unittest.main()
