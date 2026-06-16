from typing import Optional, List
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from bot.utils.logger import logger


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_user(
        self,
        user_id: int,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML",
    ) -> bool:
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to notify user {user_id}: {e}")
            return False

    async def notify_admins(
        self,
        admin_ids: List[int],
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
    ) -> int:
        sent = 0
        for admin_id in admin_ids:
            success = await self.notify_user(admin_id, text, keyboard)
            if success:
                sent += 1
        return sent

    async def broadcast(
        self,
        user_ids: List[int],
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
    ) -> tuple[int, int]:
        sent = 0
        failed = 0
        for user_id in user_ids:
            success = await self.notify_user(user_id, text, keyboard)
            if success:
                sent += 1
            else:
                failed += 1
        return sent, failed
