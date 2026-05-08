import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TradeJournal:
    def __init__(self, filepath: str = "src/data/trade_journal.csv"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(os.path.dirname(self.filepath)):
            os.makedirs(os.path.dirname(self.filepath))

        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "asset", "direction", "expiry",
                    "confidence", "rationale", "outcome", "pnl"
                ])

    def log_signal(self, signal_data: dict):
        """Log a new signal/trade."""
        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                signal_data.get('asset'),
                signal_data.get('action'),
                "15m", # Default
                signal_data.get('confidence'),
                signal_data.get('reasoning'),
                "PENDING",
                0.0
            ])

    def update_outcome(self, asset: str, outcome: str, pnl: float):
        """Update the last pending trade for an asset."""
        # This is a simplified implementation
        rows = []
        updated = False
        if not os.path.exists(self.filepath):
            return

        with open(self.filepath, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        for i in range(len(rows) - 1, 0, -1):
            if rows[i][1] == asset and rows[i][6] == "PENDING":
                rows[i][6] = outcome
                rows[i][7] = pnl
                updated = True
                break

        if updated:
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            logger.info(f"Updated journal for {asset}: {outcome}")
