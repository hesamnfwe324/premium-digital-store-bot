from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Order, OrderStatus, Payment, PaymentStatus
from bot.keyboards.admin import get_admin_keyboard
from config import settings
from bot.utils.helpers import format_price, format_datetime

router = Router()


def admin_only(func):
    from functools import wraps
    @wraps(func)
    async def wrapper(callback: CallbackQuery, *args, **kwargs):
        if callback.from_user.id not in settings.admin_list:
            await callback.answer("⛔ Unauthorized", show_alert=True)
            return
        return await func(callback, *args, **kwargs)
    return wrapper


@router.callback_query(F.data == "admin:menu")
@admin_only
async def handle_admin_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "🔐 <b>Admin Panel</b>",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "🔐 <b>Admin Panel</b>",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "admin:dashboard")
@admin_only
async def handle_admin_dashboard(callback: CallbackQuery, session: AsyncSession):
    users_result = await session.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0

    orders_result = await session.execute(select(func.count(Order.id)))
    total_orders = orders_result.scalar() or 0

    revenue_result = await session.execute(
        select(func.sum(Order.final_price)).where(Order.status == OrderStatus.DELIVERED)
    )
    total_revenue = revenue_result.scalar() or 0.0

    pending_payments_result = await session.execute(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatus.SUBMITTED)
    )
    pending_payments = pending_payments_result.scalar() or 0

    delivered_result = await session.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED)
    )
    delivered_orders = delivered_result.scalar() or 0

    text = (
        "📊 <b>Admin Dashboard</b>\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📦 Total Orders: <b>{total_orders}</b>\n"
        f"✅ Delivered: <b>{delivered_orders}</b>\n"
        f"💰 Total Revenue: <b>${format_price(total_revenue)} USDT</b>\n"
        f"⚠️ Pending Payments: <b>{pending_payments}</b>"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:pending_payments")
@admin_only
async def handle_admin_pending_payments(callback: CallbackQuery, session: AsyncSession):
    result = await session.execute(
        select(Payment).where(Payment.status == PaymentStatus.SUBMITTED)
        .order_by(Payment.created_at.asc()).limit(15)
    )
    payments = list(result.scalars().all())

    if not payments:
        await callback.answer("No pending payments.", show_alert=True)
        return

    from bot.keyboards.payment import get_payment_confirm_keyboard
    buttons = []
    for p in payments:
        buttons.append([InlineKeyboardButton(
            text=f"💳 ${p.amount_usdt:.2f} {p.currency.value} — {format_datetime(p.created_at)[:10]}",
            callback_data=f"admin_pay_detail:{p.id}",
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:menu")])

    await callback.message.edit_text(
        f"💳 <b>Pending Payments ({len(payments)})</b>\n\nSelect to confirm or reject:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_pay_detail:"))
@admin_only
async def handle_admin_pay_detail(callback: CallbackQuery, session: AsyncSession):
    payment_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        await callback.answer("Payment not found.", show_alert=True)
        return

    from bot.keyboards.payment import get_payment_confirm_keyboard
    text = (
        f"💳 <b>Payment #{payment.id}</b>\n\n"
        f"👤 User: <code>{payment.user_telegram_id}</code>\n"
        f"💵 Amount: <b>${payment.amount_usdt:.2f} USDT</b>\n"
        f"🌐 Network: <b>{payment.currency.value}</b>\n"
        f"📋 TXID: <code>{payment.txid or payment.transaction_link or 'N/A'}</code>\n"
        f"📅 Submitted: {format_datetime(payment.created_at)}"
    )
    kb = get_payment_confirm_keyboard(payment_id)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


def _back_to_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back to Admin", callback_data="admin:menu")]
    ])


@router.callback_query(F.data == "admin:discounts")
@admin_only
async def handle_admin_discounts(callback: CallbackQuery, session: AsyncSession):
    from database.models import DiscountCode
    result = await session.execute(
        select(DiscountCode).order_by(DiscountCode.created_at.desc()).limit(15)
    )
    codes = list(result.scalars().all())

    if not codes:
        text = "🎫 <b>Discount Codes</b>\n\nNo discount codes found."
    else:
        text = "🎫 <b>Discount Codes</b>\n\n"
        for dc in codes:
            status = "✅" if dc.is_active else "❌"
            text += f"{status} <code>{dc.code}</code> — {dc.discount_value}"
            if dc.discount_type.value == "percentage":
                text += "%"
            else:
                text += " USDT"
            text += f" (used: {dc.used_count})\n"

    try:
        await callback.message.edit_text(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:referrals")
@admin_only
async def handle_admin_referrals(callback: CallbackQuery, session: AsyncSession):
    from database.models import Referral
    total_result = await session.execute(select(func.count(Referral.id)))
    total = total_result.scalar() or 0

    text = (
        f"🎯 <b>Referral Stats</b>\n\n"
        f"Total Referrals: <b>{total}</b>\n\n"
        "Referral bonus: <b>5%</b> per purchase"
    )
    try:
        await callback.message.edit_text(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:tickets")
@admin_only
async def handle_admin_tickets(callback: CallbackQuery, session: AsyncSession):
    from database.models import Ticket, TicketStatus
    result = await session.execute(
        select(Ticket).where(Ticket.status == TicketStatus.OPEN)
        .order_by(Ticket.created_at.desc()).limit(15)
    )
    tickets = list(result.scalars().all())

    if not tickets:
        text = "🎫 <b>Support Tickets</b>\n\nNo open tickets."
    else:
        text = f"🎫 <b>Open Tickets ({len(tickets)})</b>\n\n"
        for t in tickets:
            text += f"🟢 <code>#{t.ticket_number}</code> — {t.subject[:40]}\n"

    try:
        await callback.message.edit_text(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:settings")
@admin_only
async def handle_admin_settings(callback: CallbackQuery):
    text = (
        "⚙️ <b>Bot Settings</b>\n\n"
        "Configure your bot settings via environment variables in your deployment.\n\n"
        "Key settings:\n"
        "• <code>BOT_TOKEN</code> — Telegram Bot Token\n"
        "• <code>ADMIN_IDS</code> — Admin Telegram IDs (comma-separated)\n"
        "• <code>WEBHOOK_HOST</code> — Your deployment URL\n"
        "• Crypto wallet addresses (USDT_TRC20_ADDRESS, etc.)"
    )
    try:
        await callback.message.edit_text(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=_back_to_admin_kb(), parse_mode="HTML")
    await callback.answer()
