from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from bot.keyboards.admin import get_admin_user_keyboard
from bot.services.user_service import UserService
from config import settings
from bot.utils.helpers import format_datetime

router = Router()


class UserSearchStates(StatesGroup):
    waiting_for_user_id = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_list


@router.callback_query(F.data == "admin:users")
async def handle_admin_users(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    await state.set_state(UserSearchStates.waiting_for_user_id)
    await callback.message.answer(
        "👥 <b>User Management</b>\n\nEnter <b>Telegram User ID</b> to search:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(UserSearchStates.waiting_for_user_id)
async def handle_user_search(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    await state.clear()

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Invalid user ID. Please send a number.")
        return

    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        await message.answer(f"❌ User {user_id} not found.")
        return

    text = (
        f"👤 <b>User Profile</b>\n\n"
        f"🆔 ID: <code>{user.telegram_id}</code>\n"
        f"👤 Name: {user.full_name}\n"
        f"🔗 Username: @{user.username or 'N/A'}\n"
        f"🌐 Language: {user.language_code}\n"
        f"📦 Orders: {user.total_orders}\n"
        f"💰 Spent: ${user.total_spent:.2f}\n"
        f"🚫 Banned: {'Yes' if user.is_banned else 'No'}\n"
        f"📅 Joined: {format_datetime(user.created_at)}"
    )
    kb = get_admin_user_keyboard(user.telegram_id, user.is_banned)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("admin_user:ban:"))
async def handle_ban_user(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    user_id = int(callback.data.split(":")[2])
    service = UserService(session)
    await service.ban_user(user_id)
    await session.commit()
    await callback.answer(f"🚫 User {user_id} banned.", show_alert=True)


@router.callback_query(F.data.startswith("admin_user:unban:"))
async def handle_unban_user(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    user_id = int(callback.data.split(":")[2])
    service = UserService(session)
    await service.unban_user(user_id)
    await session.commit()
    await callback.answer(f"✅ User {user_id} unbanned.", show_alert=True)
