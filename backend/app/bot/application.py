"""Build and configure the python-telegram-bot Application."""
import logging

from telegram.ext import Application, CommandHandler

from app.core.config import settings

logger = logging.getLogger(__name__)

_application: Application | None = None


def build_application() -> Application | None:
    """Create the bot Application. Returns None when token is not configured."""
    if not settings.telegram_bot_token:
        logger.warning(
            "TELEGRAM_BOT_TOKEN is not set — Telegram bot will not start."
        )
        return None

    from app.bot.handlers import cmd_start, cmd_link, cmd_unlink, cmd_status, cmd_help

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("link", cmd_link))
    app.add_handler(CommandHandler("unlink", cmd_unlink))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_help))

    return app


def get_application() -> Application | None:
    return _application


async def start_bot() -> None:
    """Initialize and start polling. Called from FastAPI lifespan."""
    global _application
    _application = build_application()
    if _application is None:
        return
    await _application.initialize()
    await _application.start()
    await _application.updater.start_polling(drop_pending_updates=True)
    logger.info("Telegram bot started (polling).")


async def stop_bot() -> None:
    """Stop the bot. Called from FastAPI lifespan."""
    global _application
    if _application is None:
        return
    await _application.updater.stop()
    await _application.stop()
    await _application.shutdown()
    logger.info("Telegram bot stopped.")
