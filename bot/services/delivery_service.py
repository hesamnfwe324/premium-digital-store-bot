from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import (
    Order, OrderStatus, Product, ProductCategory,
    GiftCard, VisaCard, MasterCard
)
from bot.utils.logger import logger
from datetime import datetime, timezone


class DeliveryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def deliver_order(self, order_id: int) -> Optional[str]:
        order_result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order_result.scalar_one_or_none()
        if not order:
            logger.error(f"Order not found: {order_id}")
            return None

        product_result = await self.session.execute(
            select(Product).where(Product.id == order.product_id)
        )
        product = product_result.scalar_one_or_none()
        if not product:
            return None

        content = await self._get_inventory_item(product, order.id)
        if not content:
            logger.warning(f"No inventory available for product {product.id} order {order_id}")
            return None

        order.status = OrderStatus.DELIVERED
        order.delivered_content = content
        order.delivered_at = datetime.now(timezone.utc)
        product.quantity = max(0, product.quantity - order.quantity)
        await self.session.flush()

        logger.info(f"Order {order.order_number} delivered successfully")
        return content

    async def _get_inventory_item(self, product: Product, order_id: int) -> Optional[str]:
        if product.category == ProductCategory.GIFT_CARD:
            return await self._deliver_gift_card(product.id, order_id)
        elif product.category == ProductCategory.VISA:
            return await self._deliver_visa_card(product.id, order_id)
        elif product.category == ProductCategory.MASTERCARD:
            return await self._deliver_master_card(product.id, order_id)
        return None

    async def _deliver_gift_card(self, product_id: int, order_id: int) -> Optional[str]:
        result = await self.session.execute(
            select(GiftCard).where(
                GiftCard.product_id == product_id,
                GiftCard.is_sold == False
            ).limit(1)
        )
        card = result.scalar_one_or_none()
        if not card:
            return None
        card.is_sold = True
        card.order_id = order_id
        card.sold_at = datetime.now(timezone.utc)
        await self.session.flush()
        lines = [f"🎁 Gift Card Code: {card.code}"]
        if card.pin:
            lines.append(f"📌 PIN: {card.pin}")
        if card.value:
            lines.append(f"💵 Value: {card.value}")
        return "\n".join(lines)

    async def _deliver_visa_card(self, product_id: int, order_id: int) -> Optional[str]:
        result = await self.session.execute(
            select(VisaCard).where(
                VisaCard.product_id == product_id,
                VisaCard.is_sold == False
            ).limit(1)
        )
        card = result.scalar_one_or_none()
        if not card:
            return None
        card.is_sold = True
        card.order_id = order_id
        card.sold_at = datetime.now(timezone.utc)
        await self.session.flush()
        lines = ["💳 Visa Card Details:"]
        if card.card_number:
            lines.append(f"Card Number: {card.card_number}")
        if card.expiry_month and card.expiry_year:
            lines.append(f"Expiry: {card.expiry_month}/{card.expiry_year}")
        if card.cvv:
            lines.append(f"CVV: {card.cvv}")
        if card.cardholder_name:
            lines.append(f"Cardholder: {card.cardholder_name}")
        if card.billing_address:
            lines.append(f"Billing: {card.billing_address}")
        if card.extra_info:
            lines.append(f"Info: {card.extra_info}")
        return "\n".join(lines)

    async def _deliver_master_card(self, product_id: int, order_id: int) -> Optional[str]:
        result = await self.session.execute(
            select(MasterCard).where(
                MasterCard.product_id == product_id,
                MasterCard.is_sold == False
            ).limit(1)
        )
        card = result.scalar_one_or_none()
        if not card:
            return None
        card.is_sold = True
        card.order_id = order_id
        card.sold_at = datetime.now(timezone.utc)
        await self.session.flush()
        lines = ["💳 MasterCard Details:"]
        if card.card_number:
            lines.append(f"Card Number: {card.card_number}")
        if card.expiry_month and card.expiry_year:
            lines.append(f"Expiry: {card.expiry_month}/{card.expiry_year}")
        if card.cvv:
            lines.append(f"CVV: {card.cvv}")
        if card.cardholder_name:
            lines.append(f"Cardholder: {card.cardholder_name}")
        if card.extra_info:
            lines.append(f"Info: {card.extra_info}")
        return "\n".join(lines)

    async def add_gift_card_stock(self, product_id: int, code: str, pin: Optional[str], brand: str, value: Optional[str], added_by: int) -> GiftCard:
        card = GiftCard(
            product_id=product_id,
            code=code,
            pin=pin,
            brand=brand,
            value=value,
            added_by=added_by,
        )
        self.session.add(card)
        await self.session.flush()
        return card

    async def add_visa_card_stock(self, product_id: int, data: dict, added_by: int) -> VisaCard:
        card = VisaCard(product_id=product_id, added_by=added_by, **data)
        self.session.add(card)
        await self.session.flush()
        return card

    async def add_master_card_stock(self, product_id: int, data: dict, added_by: int) -> MasterCard:
        card = MasterCard(product_id=product_id, added_by=added_by, **data)
        self.session.add(card)
        await self.session.flush()
        return card
