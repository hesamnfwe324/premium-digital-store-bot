from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from bot.keyboards.account import get_back_keyboard
from bot.services.loyalty_service import get_tier_for_spend, get_next_tier
from bot.utils.i18n import get_text
from bot.utils.helpers import format_price

router = Router()

TIER_LABEL_KEYS = {
    "bronze": "loyalty_tier_bronze",
    "silver": "loyalty_tier_silver",
    "gold": "loyalty_tier_gold",
    "platinum": "loyalty_tier_platinum",
}


@router.callback_query(F.data == "menu:loyalty")
async def handle_loyalty(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user = result.scalar_one_or_none()
    if not user:
        await callback.answer("Account not found.", show_alert=True)
        return

    tier = get_tier_for_spend(user.total_spent)
    next_tier = get_next_tier(user.total_spent)

    if next_tier:
        remaining = max(0.0, next_tier.threshold - user.total_spent)
        progress_line = get_text(
            "loyalty_progress_line", user_lang,
            remaining=format_price(remaining),
            next_tier=get_text(TIER_LABEL_KEYS[next_tier.key], user_lang),
        )
    else:
        progress_line = get_text("loyalty_max_tier_line", user_lang)

    text = get_text(
        "loyalty_title", user_lang,
        tier_emoji=tier.emoji,
        tier_name=get_text(TIER_LABEL_KEYS[tier.key], user_lang),
        spent=format_price(user.total_spent),
        bonus=f"{tier.bonus_percent:.0f}",
        progress_line=progress_line,
    )

    kb = get_back_keyboard(user_lang, callback="menu:my_account")
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
