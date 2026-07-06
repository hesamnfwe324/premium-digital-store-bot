from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Referral, Wallet, Transaction, TransactionType, User
from bot.services.loyalty_service import get_referral_bonus_percent
from bot.utils.logger import logger
from datetime import datetime, timezone

# Fallback used only if the referrer's user record can't be found.
REFERRAL_BONUS_PERCENT = 5.0


class ReferralService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_referral_count(self, referrer_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == referrer_id)
        )
        return result.scalar() or 0

    async def get_total_referral_earnings(self, referrer_id: int) -> float:
        result = await self.session.execute(
            select(func.sum(Referral.bonus_earned)).where(Referral.referrer_id == referrer_id)
        )
        return result.scalar() or 0.0

    async def process_referral_bonus(self, referrer_id: int, purchase_amount: float) -> float:
        user_result = await self.session.execute(
            select(User).where(User.telegram_id == referrer_id)
        )
        referrer = user_result.scalar_one_or_none()
        bonus_percent = get_referral_bonus_percent(referrer.total_spent) if referrer else REFERRAL_BONUS_PERCENT
        bonus = purchase_amount * (bonus_percent / 100)

        wallet_result = await self.session.execute(
            select(Wallet).where(Wallet.user_telegram_id == referrer_id)
        )
        wallet = wallet_result.scalar_one_or_none()
        if not wallet:
            return 0.0

        balance_before = wallet.balance
        wallet.balance += bonus
        wallet.total_earned_referral += bonus

        tx = Transaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.REFERRAL_BONUS,
            amount=bonus,
            balance_before=balance_before,
            balance_after=wallet.balance,
            description=f"Referral bonus: {bonus_percent:.0f}% of ${purchase_amount:.2f}",
        )
        self.session.add(tx)
        await self.session.flush()

        referral_result = await self.session.execute(
            select(Referral).where(
                Referral.referrer_id == referrer_id,
                Referral.bonus_paid == False,
            ).limit(1)
        )
        referral = referral_result.scalar_one_or_none()
        if referral:
            referral.bonus_earned += bonus
            referral.bonus_paid = True
            referral.bonus_paid_at = datetime.now(timezone.utc)
        await self.session.flush()

        logger.info(f"Referral bonus: {referrer_id} earned ${bonus:.2f}")
        return bonus
