from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Order, Product
from bot.services.review_service import ReviewService
from bot.keyboards.account import get_back_keyboard
from bot.utils.i18n import get_text

router = Router()


class ReviewStates(StatesGroup):
    waiting_for_comment = State()


def _stars_keyboard(order_id: int) -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton(text="⭐" * i, callback_data=f"rate_stars:{order_id}:{i}")
        for i in range(1, 6)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row])


@router.callback_query(F.data.startswith("rate_order:"))
async def handle_rate_order_start(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    order_id = int(callback.data.split(":")[1])
    review_service = ReviewService(session)
    can_review = await review_service.can_review(callback.from_user.id, order_id)
    if not can_review:
        already = await review_service.has_reviewed_order(order_id)
        key = "review_already_submitted" if already else "review_not_eligible"
        await callback.answer(get_text(key, user_lang), show_alert=True)
        return

    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        await callback.answer(get_text("review_not_eligible", user_lang), show_alert=True)
        return

    text = get_text("rate_order_prompt", user_lang, order_number=order.order_number)
    await callback.message.answer(text, reply_markup=_stars_keyboard(order_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("rate_stars:"))
async def handle_rate_stars(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user_lang: str = "en"):
    _, order_id_str, rating_str = callback.data.split(":")
    order_id = int(order_id_str)
    rating = int(rating_str)

    review_service = ReviewService(session)
    can_review = await review_service.can_review(callback.from_user.id, order_id)
    if not can_review:
        already = await review_service.has_reviewed_order(order_id)
        key = "review_already_submitted" if already else "review_not_eligible"
        await callback.answer(get_text(key, user_lang), show_alert=True)
        return

    await state.set_state(ReviewStates.waiting_for_comment)
    await state.update_data(order_id=order_id, rating=rating)

    text = get_text("rate_thanks_for_stars", user_lang, stars="⭐" * rating)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_skip", user_lang), callback_data=f"rate_skip:{order_id}:{rating}")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


async def _save_review(session: AsyncSession, order_id: int, user_telegram_id: int, rating: int, comment: str = None):
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    review_service = ReviewService(session)
    review = await review_service.add_review(
        product_id=order.product_id,
        user_telegram_id=user_telegram_id,
        rating=rating,
        comment=comment,
        order_id=order_id,
    )
    await session.commit()
    return review


@router.callback_query(F.data.startswith("rate_skip:"))
async def handle_rate_skip(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user_lang: str = "en"):
    _, order_id_str, rating_str = callback.data.split(":")
    order_id = int(order_id_str)
    rating = int(rating_str)

    await _save_review(session, order_id, callback.from_user.id, rating)
    await state.clear()

    text = get_text("review_submitted", user_lang)
    try:
        await callback.message.edit_text(text, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.message(ReviewStates.waiting_for_comment)
async def handle_review_comment(message: Message, state: FSMContext, session: AsyncSession, user_lang: str = "en"):
    data = await state.get_data()
    order_id = data.get("order_id")
    rating = data.get("rating")
    comment = message.text.strip() if message.text else None

    await _save_review(session, order_id, message.from_user.id, rating, comment)
    await state.clear()

    text = get_text("review_submitted", user_lang)
    await message.answer(text, reply_markup=get_back_keyboard(user_lang), parse_mode="HTML")
