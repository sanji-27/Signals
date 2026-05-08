import logging
from config.config import Config

logger = logging.getLogger(__name__)

class RiskManagerAgent:
    def __init__(self, initial_balance: float):
        self.balance = initial_balance
        self.daily_start_balance = initial_balance
        self.consecutive_losses = 0
        self.daily_loss = 0.0

    def approve_trade(self, confidence: float) -> bool:
        """Check if a trade is allowed based on risk rules."""
        if confidence < Config.MIN_CONFIDENCE:
            logger.info(f"Trade rejected: Confidence {confidence} below minimum {Config.MIN_CONFIDENCE}")
            return False

        if self.daily_loss >= Config.MAX_DAILY_LOSS * self.daily_start_balance:
            logger.warning("Trade rejected: Daily drawdown limit reached")
            return False

        if self.consecutive_losses >= Config.MAX_CONSECUTIVE_LOSSES:
            logger.warning("Trade rejected: Max consecutive losses reached")
            return False

        return True

    def calculate_position_size(self) -> float:
        """Calculate trade amount based on account risk."""
        amount = self.balance * Config.MAX_RISK_PER_TRADE
        # Ensure minimum trade amount (e.g., $1)
        return max(amount, 1.0)

    def record_result(self, pnl: float):
        """Update risk metrics after a trade."""
        self.balance += pnl
        if pnl < 0:
            self.consecutive_losses += 1
            self.daily_loss += abs(pnl)
        else:
            self.consecutive_losses = 0

    def reset_daily(self, current_balance: float):
        """Reset daily tracking."""
        self.daily_start_balance = current_balance
        self.daily_loss = 0.0
