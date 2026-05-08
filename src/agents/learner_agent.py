import pandas as pd
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class LearnerAgent:
    """Analyzes trade history to provide insights and suggestions."""
    def __init__(self, journal_path: str = "src/data/trade_journal.csv"):
        self.journal_path = journal_path

    def generate_weekly_summary(self) -> str:
        if not os.path.exists(self.journal_path):
            return "No trade history found."

        try:
            df = pd.read_csv(self.journal_path)
            if df.empty: return "Trade journal is empty."

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            one_week_ago = datetime.now() - timedelta(days=7)
            recent_df = df[df['timestamp'] > one_week_ago]

            if recent_df.empty:
                return "No trades in the last 7 days."

            wins = len(recent_df[recent_df['outcome'] == 'WIN'])
            total = len(recent_df[recent_df['outcome'] != 'PENDING'])
            win_rate = (wins / total * 100) if total > 0 else 0

            # Find best asset
            best_asset = recent_df[recent_df['outcome'] == 'WIN']['asset'].mode()
            best_asset = best_asset.iloc[0] if not best_asset.empty else "N/A"

            summary = (
                f"📊 *Weekly Performance Summary*\n"
                f"Total Trades: {total}\n"
                f"Win Rate: {win_rate:.1f}%\n"
                f"Best Asset: {best_asset}\n"
                f"Suggestions:\n"
            )

            if win_rate < 60:
                summary += "- Consider tightening RSI thresholds.\n- Avoid trading during high volatility."
            elif win_rate > 90:
                summary += "- Strategy performing optimally. Maintain current risk levels."
            else:
                summary += "- Stable performance. Monitor MTF alignment strictly."

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error analyzing trade history."
