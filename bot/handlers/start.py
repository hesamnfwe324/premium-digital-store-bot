from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.keyboards.language import get_language_keyboard
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.i18n import get_text
from bot.utils.logger import logger

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, db_user=None, user_lang: str = "en"):
    tg_user = message.from_user
    args = message.text.split()
    referred_by_code = args[1] if len(args) > 1 else None

    user_service = UserService(session)
    user, is_new = await user_service.get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        lang=user_lang,
        referred_by_code=referred_by_code,
    )
    await session.commit()

    if is_new or not user.language_code or user.language_code == "en":
        await message.answer(
            get_text("language_selection", "en"),
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )
        logger.info(f"New user {tg_user.id} shown language selection")
    else:
        lang = user.language_code
        await message.answer(
            get_text("welcome_back", lang, name=user.full_name),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML",
        )


@router.message(Command("admin"))
async def cmd_admin(message: Message, is_admin: bool = False, user_lang: str = "en"):
    if not is_admin:
        return
    from bot.keyboards.admin import get_admin_keyboard
    await message.answer(
        "🔐 <b>Admin Panel</b>\n\nWelcome back, Admin.",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message, user_lang: str = "en"):
    help_text = (
        "🤖 <b>Available Commands</b>\n\n"
        "/start — Start the bot\n"
        "/help — Show this help\n"
        "/admin — Admin panel (admins only)"
    )
    await message.answer(help_text, parse_mode="HTML")
