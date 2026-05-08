import asyncio
import logging
import signal
from config.config import Config
from src.agents.data_agent import DataAgent
from src.agents.analyst_agent import TechnicalAnalystAgent
from src.agents.ensemble_agent import MarketRegimeAgent, EnsembleOracleAgent
from src.agents.news_agent import NewsAgent
from src.agents.risk_manager import RiskManagerAgent
from src.utils.notifier import TelegramNotifier
from src.utils.journal import TradeJournal

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
        self.risk_manager = RiskManagerAgent(initial_balance=1000.0)
        self.journal = TradeJournal()

        # Link trade results to risk manager and journal
        self.data_agent.on_trade_result = self.handle_trade_result

    def handle_trade_result(self, asset: str, outcome: str, pnl: float):
        """Update bot state when a trade closes."""
        self.risk_manager.record_result(pnl)
        self.journal.update_outcome(asset, outcome, pnl)
        logger.info(f"Updated bot state for {asset}. New balance: {self.risk_manager.balance}")

    async def start(self):
        logger.info("Starting Multi-Agent Trading Bot...")
        await self.data_agent.start()

        logger.info("Bot is active and monitoring markets...")

        try:
            while True:
                # Reset daily risk at midnight (simplified)
                # self.risk_manager.reset_daily(self.risk_manager.balance)

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
                            # Log signal
                            self.journal.log_signal(decision)
                            # Notify
                            await self.notifier.send_signal(decision)
                            logger.info(f"SIGNAL DETECTED: {asset} {decision['action']} at {decision['confidence']*100}% confidence")

                            # Note: To fully close the loop, we'd place the trade here
                            # await self.data_agent.client.trade.place_trade(...)

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
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass

    bot_task = asyncio.create_task(bot.start())
    await stop_event.wait()
    bot_task.cancel()
    await bot_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
