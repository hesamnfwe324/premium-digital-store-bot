from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Referral
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.account import get_settings_keyboard, get_support_keyboard, get_back_keyboard
from bot.utils.i18n import get_text
from config import settings

router = Router()

GIFT_REWARD_THRESHOLD = 30


@router.callback_query(F.data == "menu:home")
async def handle_home(callback: CallbackQuery, user_lang: str = "en"):
    try:
        await callback.message.edit_text(
            get_text("home", user_lang),
            reply_markup=get_main_menu_keyboard(user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            get_text("home", user_lang),
            reply_markup=get_main_menu_keyboard(user_lang),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def handle_settings(callback: CallbackQuery, user_lang: str = "en"):
    try:
        await callback.message.edit_text(
            get_text("settings", user_lang),
            reply_markup=get_settings_keyboard(user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            get_text("settings", user_lang),
            reply_markup=get_settings_keyboard(user_lang),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "menu:about")
async def handle_about(callback: CallbackQuery, user_lang: str = "en"):
    text = get_text("about", user_lang, support=settings.SUPPORT_USERNAME)
    try:
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(user_lang), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:tutorials")
async def handle_tutorials(callback: CallbackQuery, user_lang: str = "en"):
    text = get_text("tutorials", user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(user_lang), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:gift_reward")
async def handle_gift_reward(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == callback.from_user.id)
    )
    count = result.scalar() or 0
    remaining = max(0, GIFT_REWARD_THRESHOLD - count)
    filled = min(count, GIFT_REWARD_THRESHOLD)
    bar_filled = "🟩" * (filled // 3)
    bar_empty = "⬜" * ((GIFT_REWARD_THRESHOLD - filled) // 3)
    progress_bar = bar_filled + bar_empty

    if count >= GIFT_REWARD_THRESHOLD:
        text = get_text("gift_reward_earned", user_lang)
    else:
        text = get_text("gift_reward_progress", user_lang,
                        count=count,
                        remaining=remaining,
                        progress_bar=progress_bar)
    try:
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(user_lang), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=get_back_keyboard(user_lang), parse_mode="HTML")
    await callback.answer()
