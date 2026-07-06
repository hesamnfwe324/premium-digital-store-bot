from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, Wallet
from bot.keyboards.account import get_account_keyboard, get_back_keyboard, get_wallet_keyboard
from bot.utils.i18n import get_text
from bot.utils.helpers import format_price, format_datetime
from config import settings

router = Router()


class DiscountStates(StatesGroup):
    waiting_for_code = State()


@router.callback_query(F.data == "menu:my_account")
async def handle_my_account(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Account not found.", show_alert=True)
        return

    text = get_text(
        "my_account", user_lang,
        name=user.full_name,
        user_id=str(user.telegram_id),
        joined=format_datetime(user.created_at)[:10],
        orders=str(user.total_orders),
        spent=format_price(user.total_spent),
    )
    kb = get_account_keyboard(user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:wallet")
async def handle_wallet(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    wallet_res = await session.execute(
        select(Wallet).where(Wallet.user_telegram_id == callback.from_user.id)
    )
    wallet = wallet_res.scalar_one_or_none()

    if not wallet:
        await callback.answer("Wallet not found.", show_alert=True)
        return

    text = get_text(
        "wallet", user_lang,
        balance=format_price(wallet.balance),
        deposited=format_price(wallet.total_deposited),
        withdrawn=format_price(wallet.total_withdrawn),
        referral=format_price(wallet.total_earned_referral),
    )
    kb = get_wallet_keyboard(user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:referral")
async def handle_referral(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    from bot.services.referral_service import ReferralService
    result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Account not found.", show_alert=True)
        return

    referral_service = ReferralService(session)
    count = await referral_service.get_referral_count(callback.from_user.id)
    earned = await referral_service.get_total_referral_earnings(callback.from_user.id)

    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user.referral_code}"

    text = get_text(
        "referral", user_lang,
        link=ref_link,
        count=str(count),
        earned=format_price(earned),
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from urllib.parse import quote
    share_text = quote(get_text("referral_share_text", user_lang))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=get_text("btn_share_referral", user_lang),
            url=f"https://t.me/share/url?url={ref_link}&text={share_text}",
        )],
        [InlineKeyboardButton(text=get_text("btn_back", user_lang), callback_data="menu:home")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:discount_codes")
async def handle_discount_codes(callback: CallbackQuery, state: FSMContext, user_lang: str = "en"):
    await state.set_state(DiscountStates.waiting_for_code)
    text = get_text("enter_discount_code", user_lang)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.message(DiscountStates.waiting_for_code)
async def handle_discount_code_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user_lang: str = "en",
):
    from bot.services.discount_service import DiscountService
    code = message.text.strip() if message.text else ""
    discount_service = DiscountService(session)

    # Pass a large amount so that min_order_amount check doesn't incorrectly
    # reject a valid code when we're only validating existence/activity.
    discount = await discount_service.validate_code(code, float("inf"))

    if not discount:
        await message.answer(get_text("invalid_discount", user_lang), parse_mode="HTML")
    else:
        saved = discount.discount_value
        if discount.discount_type.value == "percentage":
            text = get_text("discount_applied", user_lang, code=code.upper(), saved=f"{saved}%")
        else:
            text = get_text("discount_applied", user_lang, code=code.upper(), saved=format_price(saved))
        await message.answer(text, parse_mode="HTML")

    await state.clear()
