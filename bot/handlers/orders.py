from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import OrderStatus
from bot.services.order_service import OrderService
from bot.keyboards.account import get_orders_keyboard, get_back_keyboard
from bot.utils.i18n import get_text
from bot.utils.helpers import format_datetime, format_price

router = Router()

ACTIVE_STATUSES = [OrderStatus.PENDING, OrderStatus.PAYMENT_RECEIVED, OrderStatus.VALIDATING, OrderStatus.PREPARING, OrderStatus.DELIVERING]
COMPLETED_STATUSES = [OrderStatus.DELIVERED]
CANCELLED_STATUSES = [OrderStatus.CANCELLED, OrderStatus.REJECTED]


@router.callback_query(F.data == "menu:my_orders")
async def handle_my_orders(callback: CallbackQuery, user_lang: str = "en"):
    text = get_text("my_orders", user_lang)
    kb = get_orders_keyboard(user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "orders:active")
async def handle_active_orders(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    order_service = OrderService(session)
    orders = await order_service.get_user_orders(callback.from_user.id, ACTIVE_STATUSES)
    await _show_orders_list(callback, orders, "⏳ Active Orders", user_lang, "menu:my_orders")


@router.callback_query(F.data == "orders:completed")
async def handle_completed_orders(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    order_service = OrderService(session)
    orders = await order_service.get_user_orders(callback.from_user.id, COMPLETED_STATUSES)
    await _show_orders_list(callback, orders, "✅ Completed Orders", user_lang, "menu:my_orders")


@router.callback_query(F.data == "orders:cancelled")
async def handle_cancelled_orders(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    order_service = OrderService(session)
    orders = await order_service.get_user_orders(callback.from_user.id, CANCELLED_STATUSES)
    await _show_orders_list(callback, orders, "❌ Cancelled Orders", user_lang, "menu:my_orders")


async def _show_orders_list(callback, orders, title, lang, back_cb):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    if not orders:
        text = f"<b>{title}</b>\n\n{get_text('no_orders', lang)}"
        kb = get_back_keyboard(lang, back_cb)
    else:
        text = f"<b>{title}</b>\n\n"
        buttons = []
        for order in orders[:10]:
            emoji = order.status_emoji
            date_str = format_datetime(order.created_at)[:10]
            btn_text = f"{emoji} #{order.order_number} — ${format_price(order.final_price)} — {date_str}"
            buttons.append([InlineKeyboardButton(
                text=btn_text,
                callback_data=f"order_detail:{order.id}"
            )])
        buttons.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=back_cb)])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("order_detail:"))
async def handle_order_detail(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    order_id = int(callback.data.split(":")[1])
    order_service = OrderService(session)
    order = await order_service.get_order(order_id)

    if not order or order.user_telegram_id != callback.from_user.id:
        await callback.answer("Order not found.", show_alert=True)
        return

    from sqlalchemy import select
    from database.models import Product
    product_res = await session.execute(select(Product).where(Product.id == order.product_id))
    product = product_res.scalar_one_or_none()
    product_name = product.get_name(user_lang) if product else "Unknown"

    text = get_text(
        "order_status", user_lang,
        order_number=order.order_number,
        product=product_name,
        amount=format_price(order.final_price),
        emoji=order.status_emoji,
        status=order.status.value.replace("_", " ").title(),
        date=format_datetime(order.created_at),
    )

    if order.delivered_content and order.status == OrderStatus.DELIVERED:
        text += f"\n\n<b>📦 Your Product:</b>\n<code>{order.delivered_content}</code>"

    kb = get_back_keyboard(user_lang, "menu:my_orders")
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
