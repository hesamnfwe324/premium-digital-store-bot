from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Wallet, Referral
from bot.utils.helpers import generate_referral_code
from bot.utils.logger import logger
from datetime import datetime, timezone


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
        lang: str = "en",
        referred_by_code: Optional[str] = None,
    ) -> tuple[User, bool]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_activity = datetime.now(timezone.utc)
            await self.session.flush()
            return user, False

        referred_by_id = None
        if referred_by_code:
            ref_result = await self.session.execute(
                select(User).where(User.referral_code == referred_by_code)
            )
            referrer = ref_result.scalar_one_or_none()
            if referrer and referrer.telegram_id != telegram_id:
                referred_by_id = referrer.telegram_id

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=lang,
            referral_code=generate_referral_code(telegram_id),
            referred_by_id=referred_by_id,
            last_activity=datetime.now(timezone.utc),
        )
        self.session.add(user)
        await self.session.flush()

        wallet = Wallet(
            user_telegram_id=telegram_id,
            balance=0.0,
        )
        self.session.add(wallet)
        await self.session.flush()

        if referred_by_id:
            referral = Referral(
                referrer_id=referred_by_id,
                referred_id=telegram_id,
            )
            self.session.add(referral)
            await self.session.flush()

        logger.info(f"New user created: {telegram_id} ({username})")
        return user, True

    async def get_user(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def update_language(self, telegram_id: int, language_code: str) -> bool:
        user = await self.get_user(telegram_id)
        if not user:
            return False
        user.language_code = language_code
        await self.session.flush()
        return True

    async def get_total_users(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0

    async def ban_user(self, telegram_id: int) -> bool:
        user = await self.get_user(telegram_id)
        if not user:
            return False
        user.is_banned = True
        await self.session.flush()
        return True

    async def unban_user(self, telegram_id: int) -> bool:
        user = await self.get_user(telegram_id)
        if not user:
            return False
        user.is_banned = False
        await self.session.flush()
        return True
