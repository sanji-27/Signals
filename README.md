# 🚀 Olymp Trade "Sure Signal" Bot

Advanced multi-agent trading bot for Olymp Trade focusing on high-accuracy (95%+) signals using technical confluence and multi-timeframe alignment.

## 🏗️ Architecture
- **Data Agent**: Real-time WebSocket management with auto-reconnect and Alpha Vantage fallback.
- **Technical Analyst**: 50+ indicators via `pandas_ta` (Supertrend, Ichimoku, RSI, etc.).
- **Ensemble Oracle**: Reasoning agent that only approves signals meeting strict criteria.
- **Risk Manager**: Capital preservation agent (1% trade risk, 3% daily drawdown).
- **News Agent**: Sentiment analysis from global economic feeds.
- **Learner Agent**: Weekly performance auditing and retraining suggestions.

## 🛠️ Setup

1. **Clone the repository.**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   - Rename `config/.env.example` to `config/.env`.
   - Add your `OLYMP_TRADE_TOKEN`.
   - Add your `TELEGRAM_BOT_TOKEN` and `CHAT_ID`.
   - (Optional) Add `ALPHA_VANTAGE_API_KEY` for fallback data.

4. **Run the Bot**:
   ```bash
   python main.py
   ```

## ⚠️ Disclaimer
Trading involves risk. This bot is for educational and assistant purposes only. Always test in Demo mode first.
