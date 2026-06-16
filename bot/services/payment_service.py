from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Payment, PaymentStatus, CryptoCurrency, Order, OrderStatus
from bot.utils.helpers import generate_payment_reference
from config import settings
from bot.utils.logger import logger
from datetime import datetime, timezone

CRYPTO_ADDRESSES = {
    CryptoCurrency.USDT_TRC20: settings.USDT_TRC20_ADDRESS,
    CryptoCurrency.USDT_BEP20: settings.USDT_BEP20_ADDRESS,
    CryptoCurrency.BTC: settings.BTC_ADDRESS,
    CryptoCurrency.ETH: settings.ETH_ADDRESS,
    CryptoCurrency.BNB: settings.BNB_ADDRESS,
    CryptoCurrency.TON: settings.TON_ADDRESS,
}


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment(
        self,
        user_telegram_id: int,
        order_id: int,
        amount_usdt: float,
        currency: CryptoCurrency,
    ) -> Optional[Payment]:
        wallet_address = CRYPTO_ADDRESSES.get(currency, "")
        payment = Payment(
            payment_reference=generate_payment_reference(),
            user_telegram_id=user_telegram_id,
            amount_usdt=amount_usdt,
            currency=currency,
            wallet_address=wallet_address,
            status=PaymentStatus.PENDING,
        )
        self.session.add(payment)
        await self.session.flush()

        order_result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order_result.scalar_one_or_none()
        if order:
            order.payment_id = payment.id
            order.status = OrderStatus.PAYMENT_RECEIVED
            await self.session.flush()

        logger.info(f"Payment created: {payment.payment_reference} amount={amount_usdt} {currency}")
        return payment

    async def submit_txid(self, payment_id: int, txid: str) -> bool:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return False

        if txid.startswith("http"):
            payment.transaction_link = txid
        else:
            payment.txid = txid
        payment.status = PaymentStatus.SUBMITTED
        await self.session.flush()

        order_result = await self.session.execute(
            select(Order).where(Order.payment_id == payment_id)
        )
        order = order_result.scalar_one_or_none()
        if order:
            order.status = OrderStatus.VALIDATING
            await self.session.flush()

        return True

    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def confirm_payment(self, payment_id: int, admin_id: int) -> bool:
        payment = await self.get_payment(payment_id)
        if not payment:
            return False
        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_by_admin = admin_id
        payment.confirmed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def reject_payment(self, payment_id: int, admin_id: int, reason: str = "") -> bool:
        payment = await self.get_payment(payment_id)
        if not payment:
            return False
        payment.status = PaymentStatus.REJECTED
        payment.admin_note = reason
        await self.session.flush()
        return True

    async def get_pending_payments(self):
        result = await self.session.execute(
            select(Payment).where(Payment.status == PaymentStatus.SUBMITTED)
            .order_by(Payment.created_at.asc())
        )
        return list(result.scalars().all())
