import asyncio
import logging
import signal
import os
from config.config import Config
from src.agents.data_agent import DataAgent
from src.agents.analyst_agent import TechnicalAnalystAgent
from src.agents.ensemble_agent import MarketRegimeAgent, EnsembleOracleAgent
from src.agents.news_agent import NewsAgent
from src.agents.risk_manager import RiskManagerAgent
from src.agents.learner_agent import LearnerAgent
from src.utils.notifier import TelegramNotifier
from src.utils.journal import TradeJournal
from src.utils.health_check import start_health_check

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OlympTradeBot")

class TradingBot:
    def __init__(self):
        Config.validate()
        self.data_agent = DataAgent(token=Config.OLYMP_TRADE_TOKEN)
        self.analyst = TechnicalAnalystAgent()
        self.regime_agent = MarketRegimeAgent()
        self.news_agent = NewsAgent()
        self.ensemble = EnsembleOracleAgent(self.analyst, self.regime_agent, self.news_agent)
        self.notifier = TelegramNotifier()
        self.risk_manager = RiskManagerAgent()
        self.journal = TradeJournal()
        self.learner = LearnerAgent()

        # Link callbacks
        self.data_agent.on_trade_result = self.handle_trade_result

    def handle_trade_result(self, asset: str, outcome: str, pnl: float):
        self.risk_manager.record_result(pnl)
        self.journal.update_outcome(asset, outcome, pnl)
        logger.info(f"Trade Result: {asset} {outcome} PnL: {pnl}")

    async def start(self):
        logger.info("🚀 Starting Advanced Multi-Agent Trading Bot...")

        # Start health check server
        asyncio.create_task(start_health_check())

        await self.data_agent.start()

        # Sync Initial Balance
        balance = self.data_agent.client.current_balance_value
        self.risk_manager.sync_balance(balance)

        logger.info("Bot is active and monitoring markets...")

        try:
            count = 0
            while True:
                # Sync balance periodically
                balance = self.data_agent.client.current_balance_value
                if balance > 0:
                    self.risk_manager.sync_balance(balance)

                # Periodic refresh and weekly summary check
                if count % 60 == 0: # Every hour
                    await self.data_agent.refresh_candles()

                if count % (60 * 24 * 7) == 0 and count > 0: # Weekly
                    summary = self.learner.generate_weekly_summary()
                    await self.notifier.send_message(summary)

                for asset in Config.ASSETS + Config.OTC_ASSETS:
                    df_5m = self.data_agent.get_latest_candles(asset, size=300, limit=100)
                    df_15m = self.data_agent.get_latest_candles(asset, size=900, limit=100)

                    if df_5m.empty or len(df_5m) < 50 or df_15m.empty or len(df_15m) < 50:
                        continue

                    df_5m = self.analyst.compute_indicators(df_5m)
                    df_15m = self.analyst.compute_indicators(df_15m)

                    decision = self.ensemble.decide(df_5m, df_15m, asset)

                    if decision['action'] != "wait":
                        if self.risk_manager.approve_trade(decision['confidence']):
                            # Calculate position size
                            amount = self.risk_manager.calculate_position_size()
                            decision['amount'] = amount

                            self.journal.log_signal(decision)
                            await self.notifier.send_signal(decision)
                            logger.info(f"✅ SIGNAL: {asset} {decision['action']} ({decision['confidence']*100:.1f}%)")

                count += 1
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Bot loop stopped")
        finally:
            await self.data_agent.stop()

async def main():
    bot = TradingBot()
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try: loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError: pass

    bot_task = asyncio.create_task(bot.start())
    await stop_event.wait()
    bot_task.cancel()
    await bot_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
