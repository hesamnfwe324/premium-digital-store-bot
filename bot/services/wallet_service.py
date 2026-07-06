from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Wallet, Transaction, TransactionType
from bot.utils.logger import logger


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_wallet(self, user_telegram_id: int) -> Optional[Wallet]:
        result = await self.session.execute(
            select(Wallet).where(Wallet.user_telegram_id == user_telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_balance(self, user_telegram_id: int) -> float:
        wallet = await self.get_wallet(user_telegram_id)
        return wallet.balance if wallet else 0.0

    async def credit(
        self,
        user_telegram_id: int,
        amount: float,
        tx_type: TransactionType = TransactionType.DEPOSIT,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Add funds to wallet and record transaction."""
        wallet = await self.get_wallet(user_telegram_id)
        if not wallet:
            logger.error(f"WalletService.credit: no wallet for user {user_telegram_id}")
            return False

        balance_before = wallet.balance
        wallet.balance += amount
        if tx_type == TransactionType.DEPOSIT:
            wallet.total_deposited += amount
        elif tx_type == TransactionType.REFERRAL_BONUS:
            wallet.total_earned_referral += amount
        await self.session.flush()

        tx = Transaction(
            wallet_id=wallet.id,
            transaction_type=tx_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            reference_id=reference_id,
            description=description,
        )
        self.session.add(tx)
        await self.session.flush()
        logger.info(
            f"Wallet credited: user={user_telegram_id} amount={amount} "
            f"type={tx_type} balance={wallet.balance}"
        )
        return True

    async def get_wallet_for_update(self, user_telegram_id: int) -> Optional[Wallet]:
        """Fetch wallet with a row-level lock (SELECT FOR UPDATE) to prevent races."""
        result = await self.session.execute(
            select(Wallet)
            .where(Wallet.user_telegram_id == user_telegram_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def debit(
        self,
        user_telegram_id: int,
        amount: float,
        tx_type: TransactionType = TransactionType.PURCHASE,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Deduct funds from wallet atomically (row-locked). Returns False if insufficient."""
        wallet = await self.get_wallet_for_update(user_telegram_id)
        if not wallet or wallet.balance < amount:
            return False

        balance_before = wallet.balance
        wallet.balance -= amount
        if tx_type == TransactionType.WITHDRAWAL:
            wallet.total_withdrawn += amount
        await self.session.flush()

        tx = Transaction(
            wallet_id=wallet.id,
            transaction_type=tx_type,
            amount=-amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            reference_id=reference_id,
            description=description,
        )
        self.session.add(tx)
        await self.session.flush()
        logger.info(
            f"Wallet debited: user={user_telegram_id} amount={amount} "
            f"type={tx_type} balance={wallet.balance}"
        )
        return True

    async def get_transactions(
        self, user_telegram_id: int, limit: int = 10
    ) -> List[Transaction]:
        """Return the most recent transactions for this user's wallet."""
        wallet = await self.get_wallet(user_telegram_id)
        if not wallet:
            return []
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.wallet_id == wallet.id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
