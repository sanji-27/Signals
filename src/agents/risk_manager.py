import logging
from config.config import Config

logger = logging.getLogger(__name__)

class RiskManagerAgent:
    """Enforces capital preservation and position sizing."""
    def __init__(self, initial_balance: float = 0.0):
        self.balance = initial_balance
        self.daily_start_balance = initial_balance
        self.consecutive_losses = 0
        self.daily_loss = 0.0
        self._is_synced = False

    def sync_balance(self, current_balance: float):
        """Update internal balance from live API."""
        if not self._is_synced or self.daily_start_balance == 0:
            self.daily_start_balance = current_balance
            self._is_synced = True

        self.balance = current_balance
        logger.info(f"RiskManager synced. Balance: {self.balance}")

    def approve_trade(self, confidence: float) -> bool:
        """Strict logic for signal approval."""
        if confidence < Config.MIN_CONFIDENCE:
            return False

        # Drawdown check
        if self.daily_start_balance > 0:
            current_drawdown = (self.daily_start_balance - self.balance) / self.daily_start_balance
            if current_drawdown >= Config.MAX_DAILY_LOSS:
                logger.warning(f"Daily drawdown limit hit: {current_drawdown*100:.2f}%")
                return False

        if self.consecutive_losses >= Config.MAX_CONSECUTIVE_LOSSES:
            logger.warning(f"Max consecutive losses hit: {self.consecutive_losses}")
            return False

        return True

    def calculate_position_size(self) -> float:
        """Return trade amount based on account risk %."""
        amount = self.balance * Config.MAX_RISK_PER_TRADE
        return round(max(amount, 1.0), 2)

    def record_result(self, pnl: float):
        """Update metrics after trade close."""
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        # Balance will be updated via sync_balance from main loop or callback
