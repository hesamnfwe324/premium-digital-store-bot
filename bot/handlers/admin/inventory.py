from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Product, GiftCard, VisaCard, MasterCard, ProductCategory
from bot.services.delivery_service import DeliveryService
from config import settings

router = Router()


class InventoryStates(StatesGroup):
    select_product = State()
    add_gift_code = State()
    add_visa_info = State()
    add_master_info = State()


@router.callback_query(F.data == "admin_product:inventory")
async def handle_inventory_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    result = await session.execute(
        select(Product).where(Product.is_active == True).order_by(Product.category, Product.name)
    )
    products = list(result.scalars().all())

    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(
            text=f"[{p.category.value}] {p.name} (qty: {p.quantity})",
            callback_data=f"inventory_add:{p.id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:products")])

    await callback.message.edit_text(
        "📦 <b>Inventory Management</b>\n\nSelect a product to add stock:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("inventory_add:"))
async def handle_inventory_add_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    product_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        await callback.answer("Product not found.", show_alert=True)
        return

    await state.update_data(product_id=product_id, category=product.category.value, product_name=product.name, gift_brand=product.gift_card_brand or "")
    await state.set_state(InventoryStates.add_gift_code if product.category == ProductCategory.GIFT_CARD else (InventoryStates.add_visa_info if product.category == ProductCategory.VISA else InventoryStates.add_master_info))

    if product.category == ProductCategory.GIFT_CARD:
        await callback.message.answer(
            f"🎁 Adding stock for <b>{product.name}</b>\n\n"
            "Send gift card code (and optionally PIN separated by |):\n"
            "Example: <code>ABCD-EFGH-1234</code>\n"
            "Or with PIN: <code>ABCD-EFGH-1234|1234</code>",
            parse_mode="HTML",
        )
    elif product.category == ProductCategory.VISA:
        await callback.message.answer(
            f"💳 Adding Visa card for <b>{product.name}</b>\n\n"
            "Send card info in this format:\n"
            "<code>CARD_NUMBER|MM|YYYY|CVV|CARDHOLDER_NAME|BILLING_ADDRESS</code>\n\n"
            "Example:\n"
            "<code>4111111111111111|12|2026|123|John Doe|123 Main St USA</code>",
            parse_mode="HTML",
        )
    else:
        await callback.message.answer(
            f"💳 Adding MasterCard for <b>{product.name}</b>\n\n"
            "Send card info:\n"
            "<code>CARD_NUMBER|MM|YYYY|CVV|CARDHOLDER_NAME|BILLING_ADDRESS</code>",
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(InventoryStates.add_gift_code)
async def handle_add_gift_code(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in settings.admin_list:
        return
    data = await state.get_data()
    product_id = data["product_id"]
    brand = data.get("gift_brand", "")
    await state.clear()

    parts = message.text.strip().split("|")
    code = parts[0].strip()
    pin = parts[1].strip() if len(parts) > 1 else None

    delivery = DeliveryService(session)
    card = await delivery.add_gift_card_stock(product_id, code, pin, brand or "Gift Card", None, message.from_user.id)
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product:
        product.quantity += 1
    await session.commit()
    await message.answer(f"✅ Gift card code added successfully! (ID: {card.id})")


@router.message(InventoryStates.add_visa_info)
async def handle_add_visa_info(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in settings.admin_list:
        return
    data = await state.get_data()
    product_id = data["product_id"]
    await state.clear()

    parts = message.text.strip().split("|")
    if len(parts) < 4:
        await message.answer("❌ Invalid format. Please use: CARD_NUMBER|MM|YYYY|CVV|NAME|ADDRESS")
        return

    card_data = {
        "card_number": parts[0].strip() if len(parts) > 0 else None,
        "expiry_month": parts[1].strip() if len(parts) > 1 else None,
        "expiry_year": parts[2].strip() if len(parts) > 2 else None,
        "cvv": parts[3].strip() if len(parts) > 3 else None,
        "cardholder_name": parts[4].strip() if len(parts) > 4 else None,
        "billing_address": parts[5].strip() if len(parts) > 5 else None,
        "card_type": "virtual",
    }
    delivery = DeliveryService(session)
    card = await delivery.add_visa_card_stock(product_id, card_data, message.from_user.id)
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product:
        product.quantity += 1
    await session.commit()
    await message.answer(f"✅ Visa card added! (ID: {card.id})")


@router.message(InventoryStates.add_master_info)
async def handle_add_master_info(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in settings.admin_list:
        return
    data = await state.get_data()
    product_id = data["product_id"]
    await state.clear()

    parts = message.text.strip().split("|")
    if len(parts) < 4:
        await message.answer("❌ Invalid format.")
        return

    card_data = {
        "card_number": parts[0].strip() if len(parts) > 0 else None,
        "expiry_month": parts[1].strip() if len(parts) > 1 else None,
        "expiry_year": parts[2].strip() if len(parts) > 2 else None,
        "cvv": parts[3].strip() if len(parts) > 3 else None,
        "cardholder_name": parts[4].strip() if len(parts) > 4 else None,
        "billing_address": parts[5].strip() if len(parts) > 5 else None,
        "card_type": "virtual",
    }
    delivery = DeliveryService(session)
    card = await delivery.add_master_card_stock(product_id, card_data, message.from_user.id)
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product:
        product.quantity += 1
    await session.commit()
    await message.answer(f"✅ MasterCard added! (ID: {card.id})")
