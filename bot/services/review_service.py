from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Review, Order, OrderStatus
from bot.utils.logger import logger


class ReviewService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def has_reviewed_order(self, order_id: int) -> bool:
        result = await self.session.execute(select(Review).where(Review.order_id == order_id))
        return result.scalar_one_or_none() is not None

    async def can_review(self, user_telegram_id: int, order_id: int) -> bool:
        result = await self.session.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_telegram_id == user_telegram_id,
                Order.status == OrderStatus.DELIVERED,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            return False
        return not await self.has_reviewed_order(order_id)

    async def add_review(
        self,
        product_id: int,
        user_telegram_id: int,
        rating: int,
        comment: Optional[str] = None,
        order_id: Optional[int] = None,
        user_display_name: Optional[str] = None,
    ) -> Review:
        rating = max(1, min(5, rating))
        review = Review(
            product_id=product_id,
            order_id=order_id,
            user_telegram_id=user_telegram_id,
            user_display_name=user_display_name,
            rating=rating,
            comment=comment,
        )
        self.session.add(review)
        await self.session.flush()
        logger.info(f"Review added: product={product_id} user={user_telegram_id} rating={rating}")
        return review

    async def get_product_reviews(self, product_id: int, limit: int = 5) -> List[Review]:
        result = await self.session.execute(
            select(Review)
            .where(Review.product_id == product_id, Review.is_approved == True)
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_rating_summary(self, product_id: int) -> Tuple[float, int]:
        result = await self.session.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(
                Review.product_id == product_id, Review.is_approved == True
            )
        )
        row = result.first()
        if not row or row[1] == 0:
            return 0.0, 0
        return round(float(row[0]), 1), int(row[1])

    async def get_best_sellers(self, limit: int = 10) -> List[Tuple[int, int]]:
        """Return list of (product_id, order_count) for delivered orders, best sellers first."""
        result = await self.session.execute(
            select(Order.product_id, func.count(Order.id).label("cnt"))
            .where(Order.status == OrderStatus.DELIVERED)
            .group_by(Order.product_id)
            .order_by(func.count(Order.id).desc())
            .limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()]
