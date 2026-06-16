import time
from typing import Callable, Dict, Any, Awaitable
from collections import defaultdict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from bot.utils.logger import logger

RATE_LIMIT = 1.0
CALLBACK_RATE_LIMIT = 0.5
MAX_TRACKED_USERS = 10000


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self):
        self._user_timestamps: Dict[int, float] = defaultdict(float)
        self._callback_timestamps: Dict[int, float] = defaultdict(float)

    def _evict_old_entries(self, store: Dict[int, float], limit: float) -> None:
        """Remove entries older than 60 seconds to prevent unbounded memory growth."""
        if len(store) > MAX_TRACKED_USERS:
            now = time.monotonic()
            stale = [uid for uid, ts in store.items() if now - ts > 60]
            for uid in stale:
                del store[uid]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: int | None = None
        is_callback = False

        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id
                is_callback = True
        elif isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            is_callback = True

        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()

        if is_callback:
            self._evict_old_entries(self._callback_timestamps, CALLBACK_RATE_LIMIT)
            last_time = self._callback_timestamps[user_id]
            if now - last_time < CALLBACK_RATE_LIMIT:
                inner_cb = (
                    event.callback_query
                    if isinstance(event, Update)
                    else event
                )
                if isinstance(inner_cb, CallbackQuery):
                    try:
                        await inner_cb.answer("⚡ Please slow down!", show_alert=False)
                    except Exception:
                        pass
                return None
            self._callback_timestamps[user_id] = now
        else:
            self._evict_old_entries(self._user_timestamps, RATE_LIMIT)
            last_time = self._user_timestamps[user_id]
            if now - last_time < RATE_LIMIT:
                return None
            self._user_timestamps[user_id] = now

        return await handler(event, data)
