# OlympTrade "Sure Signal" Multi-Agent Bot

Professional, modular, self-learning trading bot for Olymp Trade.

## Features
- Multi-Agent Architecture (Data, Technical Analysis, Market Regime, News, Risk, Ensemble).
- Target 95%+ accuracy with "Sure Signals".
- Strict Risk Management (Max 1% risk per trade).
- Telegram Integration for signal notifications.
- Supports Forex, Composites, and OTC assets.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd signals
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the `olymptrade-api` library:
   ```bash
   # Since it's currently not on PyPI, install from the provided temp_olymp folder or GitHub
   pip install -e temp_olymp
   ```

4. Configure your environment:
   - Copy `config/.env.example` to `config/.env`.
   - Fill in your `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `OLYMP_TRADE_TOKEN`.

### How to get Olymp Trade Access Token
1. Open Olymp Trade in your browser and log in.
2. Open Developer Tools (F12) -> Network tab.
3. Refresh the page or perform an action.
4. Look for WebSocket connections or requests to the API.
5. In the request headers or messages, find the `token` or `ssid`.
   - *Note: Detailed instructions may vary; look for authorization headers in API calls.*

## Usage
Run the bot using:
```bash
python main.py
```

## Structure
- `src/agents/`: Specialized agents for data, analysis, and risk.
- `src/utils/`: Utility functions for logging, notifications, etc.
- `config/`: Configuration files and environment variables.
- `tests/`: Unit and integration tests.
