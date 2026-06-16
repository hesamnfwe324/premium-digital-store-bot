from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from config import settings


class AdminCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        is_admin = False
        if isinstance(event, Message) and event.from_user:
            is_admin = event.from_user.id in settings.admin_list
        data["is_admin"] = is_admin
        return await handler(event, data)
