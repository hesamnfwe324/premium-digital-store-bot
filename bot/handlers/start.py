from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Referral
from bot.services.user_service import UserService
from bot.keyboards.language import get_language_keyboard
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.i18n import get_text
from bot.utils.logger import logger

router = Router()

GIFT_REWARD_THRESHOLD = 30


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

    if is_new and referred_by_code:
        try:
            referrer_result = await session.execute(
                select(User).where(User.referral_code == referred_by_code)
            )
            referrer = referrer_result.scalar_one_or_none()
            if referrer:
                ref_count_result = await session.execute(
                    select(func.count(Referral.id)).where(Referral.referrer_id == referrer.telegram_id)
                )
                ref_count = ref_count_result.scalar() or 0
                notif_lang = referrer.language_code or "en"
                new_name = tg_user.first_name or "Someone"
                notif_text = get_text("referral_new_join", notif_lang, name=new_name, count=ref_count)
                await message.bot.send_message(referrer.telegram_id, notif_text, parse_mode="HTML")
                if ref_count == GIFT_REWARD_THRESHOLD:
                    gift_text = get_text("gift_reward_unlocked", notif_lang)
                    await message.bot.send_message(referrer.telegram_id, gift_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not send referral notification: {e}")

    if is_new:
        await message.answer(
            get_text("language_selection", "en"),
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )
        logger.info(f"New user {tg_user.id} shown language selection")
    else:
        lang = user.language_code or "en"
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
