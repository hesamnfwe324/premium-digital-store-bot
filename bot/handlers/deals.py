from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from database.models import Product
from bot.keyboards.products import get_products_keyboard
from bot.keyboards.account import get_back_keyboard
from bot.services.review_service import ReviewService
from bot.utils.i18n import get_text

router = Router()


@router.callback_query(F.data == "menu:deals")
async def handle_flash_deals(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(
        select(Product).where(
            Product.is_active == True,
            Product.original_price.isnot(None),
        )
    )
    all_deals = list(result.scalars().all())
    products = [p for p in all_deals if p.is_on_deal]

    text = get_text("flash_deals_title", user_lang)
    if not products:
        text += "\n\n" + get_text("no_flash_deals", user_lang)
        kb = get_back_keyboard(user_lang)
    else:
        earliest_end = min((p.deal_ends_at for p in products if p.deal_ends_at), default=None)
        if earliest_end:
            deadline = earliest_end if earliest_end.tzinfo else earliest_end.replace(tzinfo=timezone.utc)
            remaining = deadline - datetime.now(timezone.utc)
            hours = max(0, int(remaining.total_seconds() // 3600))
            time_left = f"{hours}h" if hours > 0 else "<1h"
            text += "\n" + get_text("flash_deal_ends_in", user_lang, time_left=time_left)
        kb = get_products_keyboard(products, user_lang, back_callback="menu:home")

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:best_sellers")
async def handle_best_sellers(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    review_service = ReviewService(session)
    ranked = await review_service.get_best_sellers(limit=10)

    text = get_text("best_sellers_title", user_lang)
    if not ranked:
        text += "\n\n" + get_text("no_best_sellers", user_lang)
        kb = get_back_keyboard(user_lang)
    else:
        product_ids = [pid for pid, _ in ranked]
        result = await session.execute(
            select(Product).where(Product.id.in_(product_ids), Product.is_active == True)
        )
        products_by_id = {p.id: p for p in result.scalars().all()}
        ordered_products = [products_by_id[pid] for pid, _ in ranked if pid in products_by_id]
        if not ordered_products:
            text += "\n\n" + get_text("no_best_sellers", user_lang)
            kb = get_back_keyboard(user_lang)
        else:
            kb = get_products_keyboard(
                ordered_products, user_lang, back_callback="menu:home",
                best_seller_ids=set(product_ids),
            )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
