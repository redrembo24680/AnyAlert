"""Telegram bot command handlers.

Commands:
  /start [CODE]  — welcome message; if CODE supplied, acts like /link CODE.
  /link CODE     — link Telegram account to an AnyAlert account.
  /unlink        — remove the Telegram link from the AnyAlert account.
  /status        — show current link status.
  /help          — list available commands.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.services import telegram_service
from app.db.session import get_db_session
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


async def _link_account(update: Update, code: str) -> None:
    """Shared logic for /start <code> and /link <code>."""
    tg_user = update.effective_user
    user_id = await telegram_service.consume_link_code(code)

    if user_id is None:
        await update.message.reply_text(
            "❌ <b>Код невірний або вже не дійсний.</b>\n\n"
            "Отримайте новий код у налаштуваннях профілю на сайті AnyAlert.",
            parse_mode="HTML",
        )
        return

    async for db in get_db_session():
        repo = UserRepository(db)
        # Make sure another user hasn't already linked this telegram_id
        existing = await repo.get_by_telegram_id(tg_user.id)
        if existing and existing.id != user_id:
            await update.message.reply_text(
                "⚠️ Цей Telegram акаунт вже прив'язаний до іншого облікового запису AnyAlert.",
                parse_mode="HTML",
            )
            return

        user = await repo.get_by_id(user_id)
        if user is None:
            await update.message.reply_text("❌ Користувача не знайдено.", parse_mode="HTML")
            return

        await repo.set_telegram(user, tg_user.id, tg_user.username)

    name = tg_user.first_name or "Користувач"
    await update.message.reply_text(
        f"✅ <b>Telegram успішно прив'язаний, {name}!</b>\n\n"
        "Тепер ви будете отримувати сповіщення про спрацювання трекерів прямо у Telegram. 🔔",
        parse_mode="HTML",
    )
    logger.info("Linked telegram_id=%s to user_id=%s", tg_user.id, user_id)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — optionally with a link code."""
    if context.args:
        code = context.args[0]
        # Support deep-link prefix: /start link_CODE
        if code.startswith("link_"):
            code = code[5:]
        await _link_account(update, code)
        return

    await update.message.reply_text(
        "👋 <b>Ласкаво просимо до AnyAlert Bot!</b>\n\n"
        "Цей бот надсилає сповіщення, коли ваші трекери на сайті <b>AnyAlert</b> спрацьовують.\n\n"
        "🔗 <b>Як прив'язати акаунт:</b>\n"
        "1. Зайдіть на сайт AnyAlert → Профіль → <i>Підключити Telegram</i>.\n"
        "2. Скопіюйте код та надішліть боту:\n"
        "   <code>/link XXXXXXXX</code>\n\n"
        "❓ Команди: /help",
        parse_mode="HTML",
    )


async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/link CODE — link Telegram to AnyAlert account."""
    if not context.args:
        await update.message.reply_text(
            "Використання: <code>/link XXXXXXXX</code>\n\n"
            "Отримайте код у профілі на сайті AnyAlert.",
            parse_mode="HTML",
        )
        return
    await _link_account(update, context.args[0])


async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/unlink — remove Telegram link from AnyAlert account."""
    tg_user = update.effective_user
    async for db in get_db_session():
        repo = UserRepository(db)
        user = await repo.get_by_telegram_id(tg_user.id)
        if user is None:
            await update.message.reply_text(
                "ℹ️ Ваш Telegram ще не прив'язаний до жодного акаунту AnyAlert.",
                parse_mode="HTML",
            )
            return
        await repo.clear_telegram(user)

    await update.message.reply_text(
        "✅ Telegram успішно від'язаний від вашого акаунту AnyAlert.\n"
        "Ви більше не отримуватимете сповіщення через цього бота.",
        parse_mode="HTML",
    )
    logger.info("Unlinked telegram_id=%s", tg_user.id)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/status — show linking status."""
    tg_user = update.effective_user
    async for db in get_db_session():
        repo = UserRepository(db)
        user = await repo.get_by_telegram_id(tg_user.id)
        if user:
            await update.message.reply_text(
                f"✅ <b>Прив'язаний акаунт:</b> {user.email}\n"
                "Сповіщення активні. 🔔",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                "❌ Цей Telegram не прив'язаний до жодного акаунту AnyAlert.\n\n"
                "Скористайтесь командою <code>/link XXXXXXXX</code>.",
                parse_mode="HTML",
            )
        return


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — list commands."""
    await update.message.reply_text(
        "<b>Доступні команди:</b>\n\n"
        "/start — привітання\n"
        "/link CODE — прив'язати Telegram до акаунту AnyAlert\n"
        "/unlink — від'язати Telegram\n"
        "/status — статус прив'язки\n"
        "/help — список команд",
        parse_mode="HTML",
    )
