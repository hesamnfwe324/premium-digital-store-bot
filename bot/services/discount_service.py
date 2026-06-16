from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import DiscountCode
from bot.utils.logger import logger


class DiscountService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_code(self, code: str, order_amount: float) -> Optional[DiscountCode]:
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.code == code.upper())
        )
        discount = result.scalar_one_or_none()
        if not discount:
            return None
        if not discount.is_valid():
            return None
        if order_amount < discount.min_order_amount:
            return None
        return discount

    async def apply_code(self, code: str) -> bool:
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.code == code.upper())
        )
        discount = result.scalar_one_or_none()
        if not discount:
            return False
        discount.used_count += 1
        await self.session.flush()
        return True

    async def create_code(
        self,
        code: str,
        discount_type: str,
        discount_value: float,
        max_uses: Optional[int] = None,
        min_order_amount: float = 0.0,
        expires_at=None,
        description: str = "",
    ) -> DiscountCode:
        from database.models import DiscountType
        dc = DiscountCode(
            code=code.upper(),
            discount_type=DiscountType(discount_type),
            discount_value=discount_value,
            max_uses=max_uses,
            min_order_amount=min_order_amount,
            expires_at=expires_at,
            description=description,
        )
        self.session.add(dc)
        await self.session.flush()
        return dc
