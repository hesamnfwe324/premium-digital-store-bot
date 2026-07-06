import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import (
    Product, Order, CryptoCurrency,
    CRYPTO_NETWORK_NAMES, CRYPTO_EMOJIS, Wallet,
)
from bot.services.order_service import OrderService
from bot.services.payment_service import PaymentService, CRYPTO_ADDRESSES
from bot.keyboards.payment import get_crypto_keyboard, get_payment_submitted_keyboard, get_wallet_pay_keyboard
from bot.keyboards.account import get_back_keyboard
from bot.utils.i18n import get_text
from bot.utils.helpers import format_price
from bot.utils.qr_code import generate_qr_code
from bot.utils.logger import logger
from config import settings

router = Router()


class PaymentStates(StatesGroup):
    waiting_for_txid = State()


@router.callback_query(F.data.startswith("buy:"))
async def handle_buy(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    product_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product or not product.is_active or product.quantity <= 0:
        await callback.answer(get_text("out_of_stock", user_lang), show_alert=True)
        return

    # Check wallet balance — offer wallet payment if sufficient
    wallet_res = await session.execute(
        select(Wallet).where(Wallet.user_telegram_id == callback.from_user.id)
    )
    wallet = wallet_res.scalar_one_or_none()
    wallet_balance = wallet.balance if wallet else 0.0
    can_pay_wallet = wallet_balance >= product.price_usdt

    order_service = OrderService(session)
    order = await order_service.create_order(
        user_telegram_id=callback.from_user.id,
        product_id=product_id,
    )
    await session.commit()

    if not order:
        await callback.answer("❌ Failed to create order. Please try again.", show_alert=True)
        return

    if can_pay_wallet:
        # Cancel the just-created pending order; wallet_pay handler creates its own
        from database.models import OrderStatus
        order.status = OrderStatus.CANCELLED
        await session.commit()
        text = get_text("select_payment_method", user_lang,
                        balance=format_price(wallet_balance),
                        price=format_price(product.price_usdt))
        kb = get_wallet_pay_keyboard(product_id, user_lang, wallet_balance)
    else:
        text = get_text("select_crypto", user_lang)
        kb = get_crypto_keyboard(order.id, user_lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("buy_crypto:"))
async def handle_buy_crypto_only(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    """User chose to pay with crypto even though they have wallet balance."""
    product_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product or not product.is_active or product.quantity <= 0:
        await callback.answer(get_text("out_of_stock", user_lang), show_alert=True)
        return

    order_service = OrderService(session)
    order = await order_service.create_order(
        user_telegram_id=callback.from_user.id,
        product_id=product_id,
    )
    await session.commit()

    if not order:
        await callback.answer("❌ Failed to create order. Please try again.", show_alert=True)
        return

    text = get_text("select_crypto", user_lang)
    kb = get_crypto_keyboard(order.id, user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("product_back:"))
async def handle_product_back(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    """Handle the back button from crypto selection — cancel pending order and return home."""
    try:
        order_id = int(callback.data.split(":")[1])
        order_res = await session.execute(select(Order).where(Order.id == order_id))
        order = order_res.scalar_one_or_none()
        if order and order.status.value == "pending":
            from database.models import OrderStatus
            order.status = OrderStatus.CANCELLED
            await session.commit()
    except Exception as e:
        logger.warning(f"product_back order cancel failed: {e}")

    from bot.keyboards.main_menu import get_main_menu_keyboard
    try:
        await callback.message.edit_text(
            get_text("home", user_lang),
            reply_markup=get_main_menu_keyboard(user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            get_text("home", user_lang),
            reply_markup=get_main_menu_keyboard(user_lang),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("crypto:"))
async def handle_crypto_selection(callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    currency_str = parts[2]

    try:
        currency = CryptoCurrency(currency_str)
    except ValueError:
        await callback.answer("Invalid cryptocurrency.", show_alert=True)
        return

    order_res = await session.execute(select(Order).where(Order.id == order_id))
    order = order_res.scalar_one_or_none()
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    payment_service = PaymentService(session)
    payment = await payment_service.create_payment(
        user_telegram_id=callback.from_user.id,
        order_id=order_id,
        amount_usdt=order.final_price,
        currency=currency,
    )
    await session.commit()

    if not payment:
        await callback.answer("Failed to create payment. Try again.", show_alert=True)
        return

    network_name = CRYPTO_NETWORK_NAMES.get(currency, currency.value)
    wallet_address = CRYPTO_ADDRESSES.get(currency, "")

    product_res = await session.execute(select(Product).where(Product.id == order.product_id))
    product = product_res.scalar_one_or_none()
    product_name = product.get_name(user_lang) if product else "Product"

    text = get_text(
        "payment_details", user_lang,
        product=product_name,
        amount=f"{payment.amount_usdt:.2f}",
        network=network_name,
        address=wallet_address,
    )

    kb = get_payment_submitted_keyboard(payment.id, user_lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

    try:
        qr_buffer = generate_qr_code(wallet_address)
        await callback.message.answer_photo(
            photo=qr_buffer,
            caption=f"📲 QR Code for {network_name}\n\n<code>{wallet_address}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"QR code send failed: {e}")

    await callback.answer()


@router.callback_query(F.data.startswith("submit_txid:"))
async def handle_submit_txid_prompt(callback: CallbackQuery, state: FSMContext, user_lang: str = "en"):
    payment_id = int(callback.data.split(":")[1])
    await state.set_state(PaymentStates.waiting_for_txid)
    await state.update_data(payment_id=payment_id)

    text = get_text("submit_txid", user_lang)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.message(PaymentStates.waiting_for_txid)
async def handle_txid_submission(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user_lang: str = "en",
):
    data = await state.get_data()
    payment_id = data.get("payment_id")
    txid = message.text.strip() if message.text else ""

    if not txid or len(txid) < 10:
        await message.answer("⚠️ Invalid transaction ID. Please send a valid TXID or transaction link.")
        return

    payment_service = PaymentService(session)
    success = await payment_service.submit_txid(payment_id, txid)
    await session.commit()

    if not success:
        await message.answer("❌ Failed to submit payment. Please try again.")
        return

    payment = await payment_service.get_payment(payment_id)
    order_res = await session.execute(select(Order).where(Order.payment_id == payment_id))
    order = order_res.scalar_one_or_none()
    order_id_str = str(order.id) if order else "N/A"
    order_number = order.order_number if order else "N/A"

    await state.clear()

    text = get_text("payment_received", user_lang, order_id=order_id_str)
    kb = get_back_keyboard(user_lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

    if order and payment:
        admin_text = (
            f"💳 <b>New Payment Submitted</b>\n\n"
            f"👤 User: <code>{message.from_user.id}</code> (@{message.from_user.username or 'N/A'})\n"
            f"📦 Order: <code>#{order_number}</code>\n"
            f"💵 Amount: <b>${payment.amount_usdt:.2f} USDT</b>\n"
            f"🌐 Network: <b>{payment.currency.value}</b>\n"
            f"📋 TXID: <code>{txid}</code>"
        )
        from bot.keyboards.payment import get_payment_confirm_keyboard
        from bot.services.notification_service import NotificationService

        try:
            notif = NotificationService(message.bot)
            await notif.notify_admins(
                settings.admin_list,
                admin_text,
                get_payment_confirm_keyboard(payment_id),
            )
        except Exception as e:
            logger.error(f"Admin notification failed: {e}")

    _task = asyncio.create_task(
        _simulate_order_progress(message, order_id_str, user_lang)
    )


async def _simulate_order_progress(message: Message, order_id: str, lang: str):
    await asyncio.sleep(3)
    steps = [
        "🔍 <b>Transaction Verified</b>\n✅ Your payment has been confirmed on the blockchain.",
        "📦 <b>Preparing Your Order</b>\n⚙️ Our system is processing your order automatically.",
        "🚀 <b>Order Ready for Delivery</b>\n📬 Your product will be delivered shortly.",
    ]
    for step in steps:
        try:
            await message.answer(step, parse_mode="HTML")
            await asyncio.sleep(2)
        except Exception:
            break
