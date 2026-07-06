from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import DiscountCode, User
from bot.utils.logger import logger

MIN_ORDER_FOR_DISCOUNT = 75.0  # Global minimum order amount for discount codes


class DiscountService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_code(self, code: str) -> Optional[DiscountCode]:
        """Find a discount code by code string (case-insensitive). Does NOT check order amount."""
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def check_code_eligibility(
        self, code: str, user_telegram_id: int
    ) -> Tuple[Optional[DiscountCode], str]:
        """
        Check code without an order amount. Returns (discount, status) where status is:
        - 'valid'       : code is valid and can be used
        - 'not_found'   : code does not exist
        - 'expired'     : code is expired or used up
        - 'not_eligible': first_order_only but user already has orders
        """
        discount = await self.find_code(code)
        if not discount:
            return None, "not_found"
        if not discount.is_valid():
            return None, "expired"
        if discount.first_order_only:
            user_result = await self.session.execute(
                select(User).where(User.telegram_id == user_telegram_id)
            )
            user = user_result.scalar_one_or_none()
            if user is None or user.total_orders > 0:
                return None, "not_eligible"
        return discount, "valid"

    async def validate_code(
        self, code: str, order_amount: float, user_telegram_id: Optional[int] = None
    ) -> Optional[DiscountCode]:
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.code == code.upper())
        )
        discount = result.scalar_one_or_none()
        if not discount:
            return None
        if not discount.is_valid():
            return None
        # Use the higher of the code's stored min_order_amount or the global minimum
        effective_min = max(discount.min_order_amount, MIN_ORDER_FOR_DISCOUNT)
        if order_amount < effective_min:
            return None
        if discount.first_order_only:
            if user_telegram_id is None:
                return None
            user_result = await self.session.execute(
                select(User).where(User.telegram_id == user_telegram_id)
            )
            user = user_result.scalar_one_or_none()
            if user is None or user.total_orders > 0:
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
        min_order_amount: float = MIN_ORDER_FOR_DISCOUNT,
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
