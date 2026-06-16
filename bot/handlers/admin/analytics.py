from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database.models import Order, OrderStatus, User, Referral, Product
from bot.keyboards.admin import get_admin_keyboard
from config import settings
from datetime import datetime, timezone, timedelta
from bot.utils.helpers import format_price

router = Router()


@router.callback_query(F.data == "admin:analytics")
async def handle_admin_analytics(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    total_users_r = await session.execute(select(func.count(User.id)))
    total_users = total_users_r.scalar() or 0

    total_orders_r = await session.execute(select(func.count(Order.id)))
    total_orders = total_orders_r.scalar() or 0

    daily_rev_r = await session.execute(
        select(func.sum(Order.final_price)).where(
            and_(Order.status == OrderStatus.DELIVERED, Order.delivered_at >= today_start)
        )
    )
    daily_rev = daily_rev_r.scalar() or 0.0

    weekly_rev_r = await session.execute(
        select(func.sum(Order.final_price)).where(
            and_(Order.status == OrderStatus.DELIVERED, Order.delivered_at >= week_start)
        )
    )
    weekly_rev = weekly_rev_r.scalar() or 0.0

    monthly_rev_r = await session.execute(
        select(func.sum(Order.final_price)).where(
            and_(Order.status == OrderStatus.DELIVERED, Order.delivered_at >= month_start)
        )
    )
    monthly_rev = monthly_rev_r.scalar() or 0.0

    total_rev_r = await session.execute(
        select(func.sum(Order.final_price)).where(Order.status == OrderStatus.DELIVERED)
    )
    total_rev = total_rev_r.scalar() or 0.0

    referral_count_r = await session.execute(select(func.count(Referral.id)))
    referral_count = referral_count_r.scalar() or 0

    text = (
        "📈 <b>Analytics Dashboard</b>\n\n"
        f"👥 <b>Users</b>\n"
        f"   Total: {total_users}\n\n"
        f"📦 <b>Orders</b>\n"
        f"   Total: {total_orders}\n\n"
        f"💰 <b>Revenue</b>\n"
        f"   Today: ${format_price(daily_rev)} USDT\n"
        f"   This Week: ${format_price(weekly_rev)} USDT\n"
        f"   This Month: ${format_price(monthly_rev)} USDT\n"
        f"   All Time: ${format_price(total_rev)} USDT\n\n"
        f"🎯 <b>Referrals</b>\n"
        f"   Total Referrals: {referral_count}"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back to Admin", callback_data="admin:menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
