from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database.models import Order, OrderStatus, Product, User
from bot.utils.helpers import generate_order_number
from bot.utils.logger import logger
from datetime import datetime, timezone, timedelta


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(
        self,
        user_telegram_id: int,
        product_id: int,
        quantity: int = 1,
        discount_code_id: Optional[int] = None,
        discount_amount: float = 0.0,
    ) -> Optional[Order]:
        product_result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one_or_none()
        if not product or product.quantity < quantity:
            return None

        total_price = product.price_usdt * quantity
        final_price = max(0.0, total_price - discount_amount)

        order = Order(
            order_number=generate_order_number(),
            user_telegram_id=user_telegram_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price_usdt,
            total_price=total_price,
            discount_amount=discount_amount,
            final_price=final_price,
            discount_code_id=discount_code_id,
            status=OrderStatus.PENDING,
        )
        self.session.add(order)
        await self.session.flush()
        logger.info(f"Order created: {order.order_number} for user {user_telegram_id}")
        return order

    async def get_order(self, order_id: int) -> Optional[Order]:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        result = await self.session.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def get_user_orders(
        self, user_telegram_id: int, status_filter: Optional[List[OrderStatus]] = None
    ) -> List[Order]:
        query = select(Order).where(Order.user_telegram_id == user_telegram_id)
        if status_filter:
            query = query.where(Order.status.in_(status_filter))
        query = query.order_by(Order.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_order_status(self, order_id: int, status: OrderStatus) -> bool:
        order = await self.get_order(order_id)
        if not order:
            return False
        order.status = status
        if status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def get_pending_orders(self) -> List[Order]:
        result = await self.session.execute(
            select(Order).where(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.VALIDATING, OrderStatus.PREPARING])
            ).order_by(Order.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_total_orders(self) -> int:
        result = await self.session.execute(select(func.count(Order.id)))
        return result.scalar() or 0

    async def get_daily_revenue(self) -> float:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        result = await self.session.execute(
            select(func.sum(Order.final_price)).where(
                and_(
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= today_start,
                    Order.delivered_at < tomorrow_start,
                )
            )
        )
        return result.scalar() or 0.0
