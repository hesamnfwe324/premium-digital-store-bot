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
    from bot.keyboards.account import get_back_keyboard
    text = get_text("tutorials", user_lang)
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
