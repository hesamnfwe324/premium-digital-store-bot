from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Ticket, TicketStatus
from bot.keyboards.account import get_support_keyboard, get_back_keyboard
from bot.utils.i18n import get_text
from bot.utils.helpers import generate_ticket_number, format_datetime

router = Router()


class TicketStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()


@router.callback_query(F.data == "menu:support")
async def handle_support(callback: CallbackQuery, user_lang: str = "en"):
    text = get_text("support", user_lang)
    kb = get_support_keyboard(user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "support:open_ticket")
async def handle_open_ticket(callback: CallbackQuery, state: FSMContext, user_lang: str = "en"):
    await state.set_state(TicketStates.waiting_for_subject)
    await callback.message.answer(
        "📋 <b>Open Support Ticket</b>\n\nPlease enter the <b>subject</b> of your issue:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(TicketStates.waiting_for_subject)
async def handle_ticket_subject(message: Message, state: FSMContext, user_lang: str = "en"):
    subject = message.text.strip()
    if len(subject) < 5:
        await message.answer("⚠️ Subject too short. Please provide more details.")
        return
    await state.update_data(subject=subject)
    await state.set_state(TicketStates.waiting_for_message)
    await message.answer(
        "💬 Now please describe your <b>issue in detail</b>:",
        parse_mode="HTML",
    )


@router.message(TicketStates.waiting_for_message)
async def handle_ticket_message(message: Message, state: FSMContext, session: AsyncSession, user_lang: str = "en"):
    data = await state.get_data()
    subject = data.get("subject", "Support Request")
    msg_text = message.text.strip()

    if len(msg_text) < 10:
        await message.answer("⚠️ Message too short. Please provide more details.")
        return

    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        user_telegram_id=message.from_user.id,
        subject=subject,
        message=msg_text,
        status=TicketStatus.OPEN,
    )
    session.add(ticket)
    await session.commit()

    text = get_text("ticket_created", user_lang, ticket_number=ticket.ticket_number, subject=subject)
    kb = get_back_keyboard(user_lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.clear()

    from bot.services.notification_service import NotificationService
    from config import settings
    admin_text = (
        f"🎫 <b>New Support Ticket</b>\n\n"
        f"👤 User: <code>{message.from_user.id}</code> (@{message.from_user.username or 'N/A'})\n"
        f"🆔 Ticket: <code>#{ticket.ticket_number}</code>\n"
        f"📋 Subject: {subject}\n"
        f"💬 Message: {msg_text[:200]}"
    )
    notif = NotificationService(message.bot)
    await notif.notify_admins(settings.admin_list, admin_text)


@router.callback_query(F.data == "support:my_tickets")
async def handle_my_tickets(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    result = await session.execute(
        select(Ticket).where(Ticket.user_telegram_id == callback.from_user.id)
        .order_by(Ticket.created_at.desc()).limit(10)
    )
    tickets = list(result.scalars().all())

    if not tickets:
        text = get_text("no_tickets", user_lang)
        kb = get_back_keyboard(user_lang, "menu:support")
    else:
        text = get_text("ticket_list", user_lang)
        status_emojis = {"open": "🟢", "in_progress": "🔵", "resolved": "✅", "closed": "⚫"}
        buttons = []
        for t in tickets:
            emoji = status_emojis.get(t.status.value, "❓")
            buttons.append([InlineKeyboardButton(
                text=f"{emoji} #{t.ticket_number} — {t.subject[:30]}",
                callback_data=f"ticket_detail:{t.id}"
            )])
        buttons.append([InlineKeyboardButton(text=get_text("btn_back", user_lang), callback_data="menu:support")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "support:faq")
async def handle_faq(callback: CallbackQuery, user_lang: str = "en"):
    text = (
        "❓ <b>Frequently Asked Questions</b>\n\n"
        "Q: How long does delivery take?\n"
        "A: Most orders are delivered instantly after payment confirmation.\n\n"
        "Q: What cryptocurrencies do you accept?\n"
        "A: USDT (TRC20/BEP20), BTC, ETH, BNB, TON.\n\n"
        "Q: My payment was submitted but order is pending?\n"
        "A: Our team reviews transactions. Please allow up to 30 minutes.\n\n"
        "Q: Can I get a refund?\n"
        "A: Contact support if there's an issue with your order.\n\n"
        "Q: How does the referral program work?\n"
        "A: Share your link and earn 5% from every purchase your referrals make."
    )
    kb = get_back_keyboard(user_lang, "menu:support")
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
