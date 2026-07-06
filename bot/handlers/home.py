from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Referral, Setting, User
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.account import get_settings_keyboard, get_support_keyboard, get_back_keyboard
from bot.utils.i18n import get_text
from config import settings

router = Router()

GIFT_REWARD_THRESHOLD = 20


async def _get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    result = await session.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting and setting.value else default


@router.callback_query(F.data == "menu:home")
async def handle_home(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    text = get_text("home", user_lang)
    result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user = result.scalar_one_or_none()
    if user and user.total_orders == 0:
        text += "\n\n" + get_text("welcome_discount_banner", user_lang)
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard(user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            text,
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
    text = get_text("about", user_lang)
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


@router.callback_query(F.data == "menu:join_channel")
async def handle_join_channel(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    channel_url = await _get_setting(session, "channel_url")
    if not channel_url:
        await callback.answer(get_text("channel_not_configured", user_lang), show_alert=True)
        return
    text = get_text("join_channel_prompt", user_lang)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_join_channel", user_lang), url=channel_url)],
        [InlineKeyboardButton(text=get_text("btn_back", user_lang), callback_data="menu:home")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:terms")
async def handle_terms(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    days = await _get_setting(session, "money_back_days", "3")
    text = get_text("terms_and_privacy", user_lang, days=days)
    terms_url = await _get_setting(session, "terms_url")
    kb_rows = []
    if terms_url:
        kb_rows.append([InlineKeyboardButton(text=get_text("btn_terms", user_lang), url=terms_url)])
    kb_rows.append([InlineKeyboardButton(text=get_text("btn_back", user_lang), callback_data="menu:home")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:gift_reward")
async def handle_gift_reward(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == callback.from_user.id)
    )
    count = result.scalar() or 0
    remaining = max(0, GIFT_REWARD_THRESHOLD - count)
    filled = min(count, GIFT_REWARD_THRESHOLD)
    bar_filled = "🟩" * (filled // 2)
    bar_empty = "⬜" * ((GIFT_REWARD_THRESHOLD - filled) // 2)
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
