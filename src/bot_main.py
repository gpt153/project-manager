"""
Telegram Bot Entry Point.

Run this script to start the Telegram bot.
"""


from src.config import settings
from src.database.connection import async_session_maker
from src.integrations.telegram_bot import OrchestratorTelegramBot


def main():
    """Start the Telegram bot"""
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

    bot = OrchestratorTelegramBot(
        token=settings.telegram_bot_token, db_session_maker=async_session_maker
    )

    print("🤖 Starting Project Orchestrator Telegram Bot...")
    print(f"📱 Environment: {settings.app_env}")
    print("✅ Bot is running. Press Ctrl+C to stop.")

    bot.run()


if __name__ == "__main__":
    main()
