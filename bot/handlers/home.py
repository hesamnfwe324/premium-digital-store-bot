from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.account import get_settings_keyboard, get_support_keyboard
from bot.utils.i18n import get_text
from config import settings

router = Router()


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
    from bot.keyboards.account import get_back_keyboard
    text = get_text("about", user_lang, support=settings.SUPPORT_USERNAME)
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:tutorials")
async def handle_tutorials(callback: CallbackQuery, user_lang: str = "en"):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from bot.keyboards.account import get_back_keyboard

    text = (
        "📚 <b>Tutorials & Guides</b>\n\n"
        "1️⃣ <b>How to Purchase a Card</b>\n"
        "   → Select category → Choose product → Pay with crypto → Receive instantly\n\n"
        "2️⃣ <b>Supported Cryptocurrencies</b>\n"
        "   → USDT TRC20, USDT BEP20, BTC, ETH, BNB, TON\n\n"
        "3️⃣ <b>How to Submit Payment</b>\n"
        "   → Send to the provided wallet address\n"
        "   → Copy the transaction ID (TXID)\n"
        "   → Submit in the bot\n\n"
        "4️⃣ <b>Delivery Times</b>\n"
        "   → Virtual cards: Instant after payment confirmation\n"
        "   → Gift cards: Instant after confirmation\n\n"
        "5️⃣ <b>Referral Program</b>\n"
        "   → Share your link → Earn 5% from purchases"
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
