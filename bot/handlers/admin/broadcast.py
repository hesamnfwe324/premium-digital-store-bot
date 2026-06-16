from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from bot.services.notification_service import NotificationService
from config import settings
from bot.utils.logger import logger

router = Router()


class BroadcastStates(StatesGroup):
    waiting_for_message = State()


@router.callback_query(F.data == "admin:broadcast")
async def handle_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.answer(
        "📢 <b>Broadcast Message</b>\n\nEnter the message to send to all users:\n\n"
        "⚠️ HTML formatting is supported.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def handle_broadcast_send(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in settings.admin_list:
        return
    await state.clear()

    result = await session.execute(
        select(User.telegram_id).where(User.is_active == True, User.is_banned == False)
    )
    user_ids = [row[0] for row in result.fetchall()]

    notif = NotificationService(message.bot)
    sent, failed = await notif.broadcast(user_ids, message.text)

    await message.answer(
        f"📢 <b>Broadcast Complete</b>\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(user_ids)}",
        parse_mode="HTML",
    )
    logger.info(f"Broadcast by admin {message.from_user.id}: {sent} sent, {failed} failed")
