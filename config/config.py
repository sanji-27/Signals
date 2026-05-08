import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

class Config:
    # API Keys
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    OLYMP_TRADE_TOKEN = os.getenv("OLYMP_TRADE_TOKEN")

    # Assets
    ASSETS = [
        "AUDCAD", "AUDJPY", "AUDUSD", "EURUSD", "EURJPY", "EURGBP",
        "EURAUD", "EURCAD", "EURCHF", "GBPUSD", "GBPAUD", "GBPCAD", "CADJPY",
        "ASIA_X", "CMDTY_X", "CRYPTO_X"
    ]

    # OTC Assets
    OTC_ASSETS = [f"{asset}_OTC" for asset in ["EURUSD", "GBPUSD", "AUDUSD"]]

    # Timeframes
    TIMEFRAMES = ["5m", "10m", "15m", "20m", "30m", "40m", "60m"]

    # Risk Management
    MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE", 0.01))
    MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", 0.03))
    MAX_CONSECUTIVE_LOSSES = int(os.getenv("MAX_CONSECUTIVE_LOSSES", 2))

    # Ensemble Confidence
    MIN_CONFIDENCE = 0.95

    @classmethod
    def validate(cls):
        if not cls.OLYMP_TRADE_TOKEN:
            print("Warning: OLYMP_TRADE_TOKEN not set in .env")
        if not cls.TELEGRAM_BOT_TOKEN:
            print("Warning: TELEGRAM_BOT_TOKEN not set in .env")
