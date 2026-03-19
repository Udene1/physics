"""
integrations/telegram_bot.py — Optional Telegram bot integration.

Sends daily study reminders and progress updates via Telegram.
Enable by setting TELEGRAM_BOT_TOKEN environment variable.
"""

import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def is_telegram_configured() -> bool:
    """Check if Telegram integration is configured."""
    return bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)


def send_telegram_message(text: str) -> bool:
    """
    Send a message via Telegram bot.

    Requires: pip install python-telegram-bot
    Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    """
    if not is_telegram_configured():
        return False

    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        }
        resp = requests.post(url, json=payload, timeout=10)
        return resp.ok
    except ImportError:
        print("⚠️ Install requests for Telegram: pip install requests")
        return False
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")
        return False


def send_daily_reminder(greeting: str) -> bool:
    """Send the daily greeting/reminder via Telegram."""
    return send_telegram_message(f"📚 *Daily Study Reminder*\n\n{greeting}")


def send_progress_update(report: str) -> bool:
    """Send a progress report via Telegram."""
    # Telegram has a 4096 char limit, truncate if needed
    if len(report) > 4000:
        report = report[:4000] + "\n\n... (truncated)"
    return send_telegram_message(f"📊 *Progress Update*\n\n{report}")
