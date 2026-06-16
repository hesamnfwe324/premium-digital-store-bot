from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Product, ProductCategory, ProductType
from bot.keyboards.admin import get_admin_products_keyboard
from config import settings

router = Router()


class AddProductStates(StatesGroup):
    name = State()
    description = State()
    category = State()
    price = State()
    quantity = State()
    delivery_time = State()
    gift_card_brand = State()


def admin_only(func):
    from functools import wraps
    @wraps(func)
    async def wrapper(callback: CallbackQuery, *args, **kwargs):
        if callback.from_user.id not in settings.admin_list:
            await callback.answer("⛔ Unauthorized", show_alert=True)
            return
        return await func(callback, *args, **kwargs)
    return wrapper


@router.callback_query(F.data == "admin:products")
@admin_only
async def handle_admin_products(callback: CallbackQuery):
    await callback.message.edit_text(
        "📦 <b>Product Management</b>",
        reply_markup=get_admin_products_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_product:list")
@admin_only
async def handle_list_products(callback: CallbackQuery, session: AsyncSession):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    result = await session.execute(
        select(Product).order_by(Product.category, Product.sort_order).limit(20)
    )
    products = list(result.scalars().all())

    if not products:
        await callback.answer("No products found.", show_alert=True)
        return

    text = "📋 <b>Products List</b>\n\n"
    buttons = []
    for p in products:
        status = "✅" if p.is_active else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} [{p.category.value}] {p.name} — ${p.price_usdt:.2f} (qty:{p.quantity})",
            callback_data=f"admin_product_detail:{p.id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="admin:products")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_product:add")
@admin_only
async def handle_add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProductStates.name)
    await callback.message.answer(
        "➕ <b>Add New Product</b>\n\nStep 1/6: Enter product <b>name</b>:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddProductStates.name)
async def add_product_name(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_list:
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProductStates.description)
    await message.answer("Step 2/6: Enter product <b>description</b>:", parse_mode="HTML")


@router.message(AddProductStates.description)
async def add_product_description(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_list:
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AddProductStates.category)
    await message.answer(
        "Step 3/6: Select <b>category</b>:\n\n"
        "1 — visa\n2 — mastercard\n3 — gift_card\n4 — premium_service\n\n"
        "Send the number:",
        parse_mode="HTML",
    )


@router.message(AddProductStates.category)
async def add_product_category(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_list:
        return
    cat_map = {"1": "visa", "2": "mastercard", "3": "gift_card", "4": "premium_service"}
    cat = cat_map.get(message.text.strip())
    if not cat:
        await message.answer("Invalid choice. Send 1, 2, 3, or 4.")
        return
    await state.update_data(category=cat)
    await state.set_state(AddProductStates.price)
    await message.answer("Step 4/6: Enter <b>price in USDT</b> (e.g. 15.99):", parse_mode="HTML")


@router.message(AddProductStates.price)
async def add_product_price(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_list:
        return
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("Invalid price. Enter a number like 15.99")
        return
    await state.update_data(price=price)
    await state.set_state(AddProductStates.quantity)
    await message.answer("Step 5/6: Enter initial <b>quantity</b>:", parse_mode="HTML")


@router.message(AddProductStates.quantity)
async def add_product_quantity(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_list:
        return
    try:
        qty = int(message.text.strip())
    except ValueError:
        await message.answer("Invalid quantity.")
        return
    await state.update_data(quantity=qty)
    await state.set_state(AddProductStates.delivery_time)
    await message.answer("Step 6/6: Enter <b>delivery time</b> (e.g. 'Instant' or '1-24 hours'):", parse_mode="HTML")


@router.message(AddProductStates.delivery_time)
async def add_product_finish(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in settings.admin_list:
        return
    data = await state.get_data()
    await state.clear()

    try:
        cat_enum = ProductCategory(data["category"])
        type_map = {
            ProductCategory.VISA: ProductType.VIRTUAL_VISA,
            ProductCategory.MASTERCARD: ProductType.VIRTUAL_MASTERCARD,
            ProductCategory.GIFT_CARD: ProductType.GIFT_CARD,
            ProductCategory.PREMIUM_SERVICE: ProductType.PREMIUM_SERVICE,
        }
        product = Product(
            name=data["name"],
            name_en=data["name"],
            description=data.get("description", ""),
            description_en=data.get("description", ""),
            category=cat_enum,
            product_type=type_map[cat_enum],
            price=data["price"],
            price_usdt=data["price"],
            quantity=data["quantity"],
            delivery_time=message.text.strip(),
            is_active=True,
        )
        session.add(product)
        await session.commit()
        await message.answer(f"✅ Product <b>{product.name}</b> added successfully!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Error adding product: {e}")


@router.callback_query(F.data.startswith("admin_product_detail:"))
async def handle_product_detail_admin(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    product_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        await callback.answer("Product not found.")
        return

    text = (
        f"📦 <b>{product.name}</b>\n\n"
        f"Category: {product.category.value}\n"
        f"Price: ${product.price_usdt:.2f}\n"
        f"Quantity: {product.quantity}\n"
        f"Active: {'✅' if product.is_active else '❌'}\n"
        f"Delivery: {product.delivery_time}"
    )
    toggle_text = "🔴 Deactivate" if product.is_active else "🟢 Activate"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_product_toggle:{product_id}")],
        [InlineKeyboardButton(text="🗑️ Delete", callback_data=f"admin_product_delete:{product_id}")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin_product:list")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_toggle:"))
async def handle_product_toggle(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    product_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product:
        product.is_active = not product.is_active
        await session.commit()
        status = "activated" if product.is_active else "deactivated"
        await callback.answer(f"Product {status}!", show_alert=True)


@router.callback_query(F.data.startswith("admin_product_delete:"))
async def handle_product_delete(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return
    product_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product:
        product.is_active = False
        await session.commit()
        await callback.answer("Product deactivated (soft delete).", show_alert=True)
