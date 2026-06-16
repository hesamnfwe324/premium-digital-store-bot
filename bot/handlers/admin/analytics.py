from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database.models import Order, OrderStatus, User, Referral
from config import settings
from datetime import datetime, timezone, timedelta
from bot.utils.helpers import format_price
from bot.utils.admin import admin_only

router = Router()


@router.callback_query(F.data == "admin:analytics")
@admin_only
async def handle_admin_analytics(callback: CallbackQuery, session: AsyncSession):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
    total_orders = (await session.execute(select(func.count(Order.id)))).scalar() or 0

    daily_rev = (await session.execute(
        select(func.sum(Order.final_price)).where(
            and_(Order.status == OrderStatus.DELIVERED, Order.delivered_at >= today_start)
        )
    )).scalar() or 0.0

    weekly_rev = (await session.execute(
        select(func.sum(Order.final_price)).where(
            and_(Order.status == OrderStatus.DELIVERED, Order.delivered_at >= week_start)
        )
    )).scalar() or 0.0

    monthly_rev = (await session.execute(
        select(func.sum(Order.final_price)).where(
            and_(Order.status == OrderStatus.DELIVERED, Order.delivered_at >= month_start)
        )
    )).scalar() or 0.0

    total_rev = (await session.execute(
        select(func.sum(Order.final_price)).where(Order.status == OrderStatus.DELIVERED)
    )).scalar() or 0.0

    referral_count = (await session.execute(select(func.count(Referral.id)))).scalar() or 0

    delivered_count = (await session.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED)
    )).scalar() or 0

    text = (
        "📈 <b>Analytics Dashboard</b>\n\n"
        f"👥 <b>Users:</b> {total_users}\n"
        f"📦 <b>Total Orders:</b> {total_orders}\n"
        f"✅ <b>Delivered:</b> {delivered_count}\n\n"
        f"💰 <b>Revenue</b>\n"
        f"   Today: <b>${format_price(daily_rev)} USDT</b>\n"
        f"   This Week: <b>${format_price(weekly_rev)} USDT</b>\n"
        f"   This Month: <b>${format_price(monthly_rev)} USDT</b>\n"
        f"   All Time: <b>${format_price(total_rev)} USDT</b>\n\n"
        f"🎯 <b>Referrals:</b> {referral_count}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back to Admin", callback_data="admin:menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
