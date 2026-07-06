from functools import wraps
from aiogram.types import CallbackQuery, Message
from config import settings


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_list


def admin_only(func):
    """Decorator that blocks non-admins from callback handlers."""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = None
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        elif isinstance(event, Message):
            user_id = event.from_user.id
        if user_id not in settings.admin_list:
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Unauthorized", show_alert=True)
            else:
                await event.answer("⛔ Unauthorized")
            return
        return await func(event, *args, **kwargs)
    return wrapper
