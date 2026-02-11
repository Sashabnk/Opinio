# Opinio Bot

Analytical platform for the Opinion.trade ecosystem.

## Features
- Monitors new markets on Opinion.trade via Open API.
- Sends Telegram notifications with referral links.
- Modular architecture (easy to add Twitter/Farcaster modules).
- SQLite backend for tracking processed markets and subscribers.

## Requirements
- Python 3.8+
- [Opinion OpenAPI Key](https://docs.google.com/forms/d/1h7gp8UffZeXzYQ-lv4jcou9PoRNOqMAQhyW4IwZDnII)
- Telegram Bot Token (from @BotFather)

## Installation
1. Clone the repository.
2. **Create and activate a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you are not using a virtual environment, use `python3 -m pip install -r requirements.txt`*

4. **Copy `.env` and fill in your tokens:**
   ```env
   BOT_TOKEN=your_telegram_bot_token
   REFERRAL_CODE=your_referral_code
   API_KEY=your_opinion_api_key
   ```

## Running
```bash
# Ensure your venv is activated (if using one)
source venv/bin/activate
python3 main.py
```

## Project Structure
- `core/`: Config and core logic.
- `services/`: Opinion API and Database services.
- `handlers/`: Telegram command handlers.
- `social/`: Future social media integration modules.
- `main.py`: Application entry point.
