from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Product, ProductCategory
from bot.keyboards.products import (
    get_products_keyboard,
    get_product_detail_keyboard,
    get_gift_card_categories_keyboard,
)
from bot.keyboards.account import get_back_keyboard
from bot.utils.i18n import get_text, normalize_delivery_time

router = Router()


@router.callback_query(F.data == "menu:visa_cards")
async def handle_visa_cards(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(
        select(Product).where(
            Product.category == ProductCategory.VISA,
            Product.is_active == True,
        ).order_by(Product.sort_order, Product.price_usdt)
    )
    products = list(result.scalars().all())

    text = get_text("visa_cards", user_lang)
    if not products:
        text += "\n\n" + get_text("no_products_available", user_lang)
        kb = get_back_keyboard(user_lang)
    else:
        kb = get_products_keyboard(products, user_lang, back_callback="menu:home")

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:mastercards")
async def handle_mastercards(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(
        select(Product).where(
            Product.category == ProductCategory.MASTERCARD,
            Product.is_active == True,
        ).order_by(Product.sort_order, Product.price_usdt)
    )
    products = list(result.scalars().all())

    text = get_text("mastercards", user_lang)
    if not products:
        text += "\n\n" + get_text("no_products_available", user_lang)
        kb = get_back_keyboard(user_lang)
    else:
        kb = get_products_keyboard(products, user_lang, back_callback="menu:home")

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:gift_cards")
async def handle_gift_cards(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(
        select(Product.gift_card_brand).where(
            Product.category == ProductCategory.GIFT_CARD,
            Product.is_active == True,
            Product.gift_card_brand.isnot(None),
        ).distinct()
    )
    brands = [row[0] for row in result.fetchall() if row[0]]

    text = get_text("gift_cards", user_lang)
    if not brands:
        text += "\n\n" + get_text("no_products_available", user_lang)
        kb = get_back_keyboard(user_lang)
    else:
        kb = get_gift_card_categories_keyboard(brands, user_lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gift_brand:"))
async def handle_gift_brand(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    brand = callback.data.split(":", 1)[1]
    result = await session.execute(
        select(Product).where(
            Product.category == ProductCategory.GIFT_CARD,
            Product.gift_card_brand.ilike(f"%{brand}%"),
            Product.is_active == True,
        ).order_by(Product.price_usdt)
    )
    products = list(result.scalars().all())
    kb = get_products_keyboard(products, user_lang, back_callback="menu:gift_cards")
    title = get_text("gift_card_brand_title", user_lang, brand=brand.title())
    try:
        await callback.message.edit_text(title, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(title, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:premium_services")
async def handle_premium_services(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    result = await session.execute(
        select(Product).where(
            Product.category == ProductCategory.PREMIUM_SERVICE,
            Product.is_active == True,
        ).order_by(Product.sort_order, Product.price_usdt)
    )
    products = list(result.scalars().all())
    text = get_text("premium_services", user_lang)
    if not products:
        text += "\n\n" + get_text("no_products_available", user_lang)
        kb = get_back_keyboard(user_lang)
    else:
        kb = get_products_keyboard(products, user_lang, back_callback="menu:home")
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def handle_product_detail(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    product_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        await callback.answer(get_text("product_not_found", user_lang), show_alert=True)
        return

    if not product.is_active:
        await callback.answer(get_text("product_unavailable", user_lang), show_alert=True)
        return

    name = product.get_name(user_lang)
    description = product.get_description(user_lang)

    if product.quantity > 0:
        stock_status = get_text("stock_available", user_lang, count=product.quantity)
    else:
        stock_status = get_text("out_of_stock_label", user_lang)

    # Normalize delivery_time: translate known instant-delivery values to user's language
    delivery = normalize_delivery_time(product.delivery_time or "", user_lang)

    text = get_text(
        "product_detail", user_lang,
        name=name,
        description=description or get_text("default_description", user_lang),
        price=f"{product.price_usdt:.2f}",
        quantity=stock_status,
        delivery=delivery,
    )

    cat_map = {
        "visa": "menu:visa_cards",
        "mastercard": "menu:mastercards",
        "gift_card": "menu:gift_cards",
        "premium_service": "menu:premium_services",
    }
    back_cb = cat_map.get(product.category.value, "menu:home")

    if product.quantity <= 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_out_of_stock", user_lang), callback_data="noop")],
            [InlineKeyboardButton(text=get_text("btn_back", user_lang), callback_data=back_cb)],
            [InlineKeyboardButton(text=get_text("btn_home", user_lang), callback_data="menu:home")],
        ])
    else:
        kb = get_product_detail_keyboard(product_id, user_lang, back_callback=back_cb)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()
