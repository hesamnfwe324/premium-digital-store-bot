from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.i18n import get_text, SUPPORTED_LANGUAGES
from bot.utils.logger import logger

router = Router()


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_selection(callback: CallbackQuery, session: AsyncSession, db_user=None):
    lang_code = callback.data.split(":")[1]
    if lang_code not in SUPPORTED_LANGUAGES:
        await callback.answer("Invalid language selection.", show_alert=True)
        return

    tg_user = callback.from_user
    user_service = UserService(session)

    user, is_new = await user_service.get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        lang=lang_code,
    )
    await user_service.update_language(tg_user.id, lang_code)
    await session.commit()

    lang_info = SUPPORTED_LANGUAGES[lang_code]
    lang_name = lang_info["native"]

    success_msg = get_text("language_changed", lang_code)
    welcome_msg = get_text("home", lang_code)

    try:
        await callback.message.edit_text(
            f"{success_msg}\n\n{welcome_msg}",
            reply_markup=get_main_menu_keyboard(lang_code),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"{success_msg}\n\n{welcome_msg}",
            reply_markup=get_main_menu_keyboard(lang_code),
            parse_mode="HTML",
        )

    await callback.answer(f"✅ {lang_name}")
    logger.info(f"User {tg_user.id} selected language: {lang_code}")


@router.callback_query(F.data == "settings:language")
async def handle_change_language(callback: CallbackQuery, user_lang: str = "en"):
    from bot.keyboards.language import get_language_keyboard
    try:
        await callback.message.edit_text(
            get_text("language_selection", user_lang),
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            get_text("language_selection", user_lang),
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )
    await callback.answer()
