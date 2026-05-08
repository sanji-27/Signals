import logging
import asyncio
from telegram import Bot
from config.config import Config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN) if Config.TELEGRAM_BOT_TOKEN else None
        self.chat_id = Config.TELEGRAM_CHAT_ID

    async def send_signal(self, signal_data: dict):
        """Send a professional signal message to Telegram."""
        if not self.bot or not self.chat_id:
            logger.warning("Telegram not configured. Signal: %s", signal_data)
            return

        message = (
            f"🚀 *SURE SIGNAL DETECTED* 🚀\n\n"
            f"Asset: *{signal_data['asset']}*\n"
            f"Direction: *{signal_data['action']}*\n"
            f"Confidence: *{signal_data['confidence']*100:.1f}%*\n"
            f"Expiry: *5-15 min*\n\n"
            f"Rationale:\n_{signal_data['reasoning']}_\n\n"
            f"Risk Level: *LOW*"
        )

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
            logger.info("Signal sent to Telegram")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def send_message(self, text: str):
        """Send a generic message."""
        if not self.bot or not self.chat_id:
            return
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
