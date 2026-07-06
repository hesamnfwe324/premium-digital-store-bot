from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import StockNotification
from bot.utils.logger import logger


class StockNotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_subscribed(self, product_id: int, user_telegram_id: int) -> bool:
        result = await self.session.execute(
            select(StockNotification).where(
                StockNotification.product_id == product_id,
                StockNotification.user_telegram_id == user_telegram_id,
                StockNotification.notified == False,
            )
        )
        return result.scalar_one_or_none() is not None

    async def subscribe(self, product_id: int, user_telegram_id: int) -> bool:
        if await self.is_subscribed(product_id, user_telegram_id):
            return False
        self.session.add(StockNotification(product_id=product_id, user_telegram_id=user_telegram_id))
        await self.session.flush()
        return True

    async def get_pending_subscribers(self, product_id: int) -> List[StockNotification]:
        result = await self.session.execute(
            select(StockNotification).where(
                StockNotification.product_id == product_id,
                StockNotification.notified == False,
            )
        )
        return list(result.scalars().all())

    async def mark_notified(self, notifications: List[StockNotification]) -> None:
        for n in notifications:
            n.notified = True
        await self.session.flush()
        logger.info(f"Marked {len(notifications)} stock notifications as sent")
