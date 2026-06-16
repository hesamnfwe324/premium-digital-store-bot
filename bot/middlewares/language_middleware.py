from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from sqlalchemy import select
from database.models import User
from database.connection import AsyncSessionLocal
from bot.utils.logger import logger

SUPPORTED_LANGS = {"en", "es", "fr", "de", "ru", "zh", "ar", "fa"}


def _extract_telegram_user(event: TelegramObject):
    """Extract the Telegram user from any event type (Update, Message, CallbackQuery, etc.)."""
    if isinstance(event, Update):
        if event.message:
            return event.message.from_user
        if event.callback_query:
            return event.callback_query.from_user
        if event.inline_query:
            return event.inline_query.from_user
        if event.my_chat_member:
            return event.my_chat_member.from_user
        if event.chat_member:
            return event.chat_member.from_user
        return None
    if isinstance(event, (Message, CallbackQuery)):
        return event.from_user
    return None


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        telegram_user = _extract_telegram_user(event)

        if not telegram_user:
            data.setdefault("user_lang", "en")
            data.setdefault("db_user", None)
            return await handler(event, data)

        user_lang = "en"

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_user.id)
                )
                db_user = result.scalar_one_or_none()

                if db_user:
                    user_lang = db_user.language_code or "en"
                    if user_lang not in SUPPORTED_LANGS:
                        user_lang = "en"
                    data["db_user"] = db_user
                else:
                    data["db_user"] = None
                    raw_lang = (telegram_user.language_code or "en")[:2].lower()
                    user_lang = raw_lang if raw_lang in SUPPORTED_LANGS else "en"

                data["session"] = session
                data["user_lang"] = user_lang

                return await handler(event, data)

            except Exception as exc:
                logger.error(f"LanguageMiddleware error for user {telegram_user.id}: {exc}")
                await session.rollback()
                raise
