from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Order, OrderStatus, Payment, PaymentStatus, User
from bot.keyboards.admin import get_admin_orders_keyboard
from bot.services.delivery_service import DeliveryService
from bot.services.notification_service import NotificationService
from bot.utils.helpers import format_price, format_datetime
from bot.utils.admin import admin_only
from bot.utils.i18n import get_text

router = Router()


async def _get_user_lang(session: AsyncSession, user_telegram_id: int) -> str:
    result = await session.execute(select(User).where(User.telegram_id == user_telegram_id))
    user = result.scalar_one_or_none()
    return user.language_code if user and user.language_code else "en"


def _rate_order_keyboard(order_id: int, user_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_rate_order", user_lang), callback_data=f"rate_order:{order_id}")],
    ])


async def _update_user_stats(session: AsyncSession, order: Order) -> None:
    try:
        res = await session.execute(select(User).where(User.telegram_id == order.user_telegram_id))
        user = res.scalar_one_or_none()
        if user:
            user.total_orders += 1
            user.total_spent += order.final_price
            await session.flush()
    except Exception:
        pass


@router.callback_query(F.data == "admin:orders")
@admin_only
async def handle_admin_orders(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛒 <b>Order Management</b>",
        reply_markup=get_admin_orders_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_orders:"))
@admin_only
async def handle_admin_orders_filter(callback: CallbackQuery, session: AsyncSession):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    filter_type = callback.data.split(":")[1]
    status_map = {
        "pending": [OrderStatus.PENDING],
        "validating": [OrderStatus.VALIDATING, OrderStatus.PREPARING, OrderStatus.DELIVERING],
        "delivered": [OrderStatus.DELIVERED],
        "rejected": [OrderStatus.REJECTED, OrderStatus.CANCELLED],
    }
    statuses = status_map.get(filter_type, [OrderStatus.PENDING])
    result = await session.execute(
        select(Order).where(Order.status.in_(statuses))
        .order_by(Order.created_at.desc()).limit(20)
    )
    orders = list(result.scalars().all())
    if not orders:
        await callback.answer("No orders found.", show_alert=True)
        return
    buttons = []
    for order in orders:
        buttons.append([InlineKeyboardButton(
            text=f"{order.status_emoji} #{order.order_number} — ${format_price(order.final_price)} — {format_datetime(order.created_at)[:10]}",
            callback_data=f"admin_order_detail:{order.id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:orders")])
    await callback.message.edit_text(
        f"📋 <b>Orders — {filter_type.title()}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_detail:"))
@admin_only
async def handle_admin_order_detail(callback: CallbackQuery, session: AsyncSession):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    order_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return
    text = (
        f"📦 <b>Order #{order.order_number}</b>\n\n"
        f"👤 User: <code>{order.user_telegram_id}</code>\n"
        f"💵 Amount: ${format_price(order.final_price)} USDT\n"
        f"{order.status_emoji} Status: {order.status.value}\n"
        f"📅 Created: {format_datetime(order.created_at)}"
    )
    kb_rows = []
    if order.status in [OrderStatus.VALIDATING, OrderStatus.PREPARING]:
        kb_rows.append([InlineKeyboardButton(text="🚀 Deliver Order", callback_data=f"admin_deliver:{order_id}")])
    if order.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
        kb_rows.append([InlineKeyboardButton(text="❌ Reject Order", callback_data=f"admin_reject_order:{order_id}")])
    kb_rows.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:orders")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_deliver:"))
@admin_only
async def handle_admin_deliver(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1])
    delivery_service = DeliveryService(session)
    content = await delivery_service.deliver_order(order_id)
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if content and order:
        await _update_user_stats(session, order)
        await session.commit()
        notif = NotificationService(callback.bot)
        user_lang = await _get_user_lang(session, order.user_telegram_id)
        user_text = (
            f"🎉 <b>Your Order Has Been Delivered!</b>\n\n"
            f"📦 Order: <code>#{order.order_number}</code>\n\n"
            f"<b>Your Product:</b>\n{content}\n\n"
            "✅ Thank you for shopping with us!"
            + get_text("order_delivered_rate_hint", user_lang)
        )
        await notif.notify_user(order.user_telegram_id, user_text, keyboard=_rate_order_keyboard(order.id, user_lang))
        await callback.answer("✅ Order delivered!", show_alert=True)
    else:
        await session.rollback()
        await callback.answer("❌ No inventory available for this product.", show_alert=True)


@router.callback_query(F.data.startswith("admin_confirm_pay:"))
@admin_only
async def handle_admin_confirm_payment(callback: CallbackQuery, session: AsyncSession):
    payment_id = int(callback.data.split(":")[1])
    from bot.services.payment_service import PaymentService
    payment_service = PaymentService(session)
    await payment_service.confirm_payment(payment_id, callback.from_user.id)
    payment = await payment_service.get_payment(payment_id)
    result = await session.execute(select(Order).where(Order.payment_id == payment_id))
    order = result.scalar_one_or_none()
    if order:
        order.status = OrderStatus.PREPARING
        await session.flush()
        delivery_service = DeliveryService(session)
        content = await delivery_service.deliver_order(order.id)
        if content:
            await _update_user_stats(session, order)
        await session.commit()
        notif = NotificationService(callback.bot)
        user_lang = await _get_user_lang(session, order.user_telegram_id)
        if content:
            user_text = (
                f"🎉 <b>Order Delivered!</b>\n\n"
                f"📦 Order: <code>#{order.order_number}</code>\n\n"
                f"<b>Your Product:</b>\n{content}\n\n"
                "✅ Thank you for shopping with us!"
                + get_text("order_delivered_rate_hint", user_lang)
            )
            await notif.notify_user(order.user_telegram_id, user_text, keyboard=_rate_order_keyboard(order.id, user_lang))
        else:
            user_text = (
                f"✅ Payment confirmed for order <code>#{order.order_number}</code>.\n"
                "Your product will be delivered shortly."
            )
            await notif.notify_user(order.user_telegram_id, user_text)
    try:
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ <b>PAYMENT CONFIRMED</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer("✅ Payment confirmed and order delivered!", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_pay:"))
@admin_only
async def handle_admin_reject_payment(callback: CallbackQuery, session: AsyncSession):
    payment_id = int(callback.data.split(":")[1])
    from bot.services.payment_service import PaymentService
    payment_service = PaymentService(session)
    await payment_service.reject_payment(payment_id, callback.from_user.id, "Rejected by admin")
    result = await session.execute(select(Order).where(Order.payment_id == payment_id))
    order = result.scalar_one_or_none()
    if order:
        order.status = OrderStatus.REJECTED
        await session.commit()
        notif = NotificationService(callback.bot)
        await notif.notify_user(
            order.user_telegram_id,
            f"❌ <b>Payment Rejected</b>\n\nOrder <code>#{order.order_number}</code> payment could not be verified. "
            "Please contact support if you believe this is an error.",
        )
    try:
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ <b>PAYMENT REJECTED</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer("❌ Payment rejected.", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_order:"))
@admin_only
async def handle_reject_order(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order:
        order.status = OrderStatus.REJECTED
        await session.commit()
        notif = NotificationService(callback.bot)
        await notif.notify_user(
            order.user_telegram_id,
            f"❌ Order <code>#{order.order_number}</code> has been rejected. Please contact support.",
        )
        await callback.answer("Order rejected.", show_alert=True)
