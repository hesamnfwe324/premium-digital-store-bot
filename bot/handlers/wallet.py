"""
Wallet top-up, transaction history, and pay-from-wallet handlers.
"""
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import (
    Wallet, Product, Order, OrderStatus, User,
    Payment, PaymentStatus, CryptoCurrency,
    CRYPTO_NETWORK_NAMES, CRYPTO_EMOJIS, TransactionType,
)
from bot.services.wallet_service import WalletService
from bot.services.payment_service import PaymentService, CRYPTO_ADDRESSES
from bot.services.order_service import OrderService
from bot.services.delivery_service import DeliveryService
from bot.services.notification_service import NotificationService
from bot.keyboards.account import get_wallet_keyboard, get_back_keyboard
from bot.utils.i18n import get_text
from bot.utils.helpers import format_price, format_datetime, generate_payment_reference
from bot.utils.qr_code import generate_qr_code
from bot.utils.logger import logger
from config import settings

router = Router()

MIN_TOPUP = 5.0  # minimum deposit in USDT


class WalletTopUpStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_txid = State()


# ─── Wallet main screen ────────────────────────────────────────────────────────

@router.callback_query(F.data == "wallet:topup")
async def handle_wallet_topup(callback: CallbackQuery, state: FSMContext, user_lang: str = "en"):
    await state.set_state(WalletTopUpStates.waiting_for_amount)
    text = get_text("wallet_topup_intro", user_lang)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "wallet:history")
async def handle_wallet_history(
    callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"
):
    wallet_svc = WalletService(session)
    txs = await wallet_svc.get_transactions(callback.from_user.id, limit=10)

    if not txs:
        text = get_text("wallet_no_history", user_lang)
    else:
        TYPE_ICONS = {
            TransactionType.DEPOSIT:       "📥",
            TransactionType.WITHDRAWAL:    "📤",
            TransactionType.PURCHASE:      "🛒",
            TransactionType.REFUND:        "🔄",
            TransactionType.REFERRAL_BONUS:"🎯",
            TransactionType.ADMIN_CREDIT:  "✅",
            TransactionType.ADMIN_DEBIT:   "⚠️",
        }
        TX_LABELS = {
            TransactionType.DEPOSIT:        get_text("wallet_tx_deposit", user_lang),
            TransactionType.WITHDRAWAL:     get_text("wallet_tx_withdrawal", user_lang),
            TransactionType.PURCHASE:       get_text("wallet_tx_purchase", user_lang),
            TransactionType.REFUND:         get_text("wallet_tx_refund", user_lang),
            TransactionType.REFERRAL_BONUS: get_text("wallet_tx_referral", user_lang),
            TransactionType.ADMIN_CREDIT:   get_text("wallet_tx_admin_credit", user_lang),
            TransactionType.ADMIN_DEBIT:    get_text("wallet_tx_admin_debit", user_lang),
        }
        lines = []
        for tx in txs:
            icon = TYPE_ICONS.get(tx.transaction_type, "💫")
            label = TX_LABELS.get(tx.transaction_type, tx.transaction_type.value)
            sign = "+" if tx.amount >= 0 else ""
            date = format_datetime(tx.created_at)[:10]
            lines.append(f"{icon} {label}  <b>{sign}{format_price(abs(tx.amount))} USDT</b>  <i>{date}</i>")

        text = get_text("wallet_history_title", user_lang, count=len(txs))
        text += "\n\n" + "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_back", user_lang), callback_data="menu:wallet")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─── Top-up amount input ────────────────────────────────────────────────────────

@router.message(WalletTopUpStates.waiting_for_amount)
async def handle_topup_amount_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user_lang: str = "en",
):
    raw = message.text.strip() if message.text else ""
    try:
        amount = float(raw.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(get_text("wallet_topup_invalid", user_lang), parse_mode="HTML")
        return

    if amount < MIN_TOPUP:
        await message.answer(
            get_text("wallet_topup_min_error", user_lang, min=format_price(MIN_TOPUP)),
            parse_mode="HTML",
        )
        return

    await state.update_data(topup_amount=amount)
    await state.clear()

    text = get_text("wallet_topup_select_crypto", user_lang, amount=format_price(amount))
    kb = _get_topup_crypto_keyboard(amount, user_lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


def _get_topup_crypto_keyboard(amount: float, lang: str) -> InlineKeyboardMarkup:
    """Crypto selection keyboard for wallet top-up (amount encoded in callback)."""
    buttons = []
    row = []
    for i, (currency, name) in enumerate(CRYPTO_NETWORK_NAMES.items()):
        emoji = CRYPTO_EMOJIS.get(currency, "💰")
        short = currency.value.replace("_", " ")
        amt_str = f"{amount:.2f}".replace(".", "_")  # dots not safe in callback data
        row.append(InlineKeyboardButton(
            text=f"{emoji} {short}",
            callback_data=f"topup_crypto:{amt_str}:{currency.value}",
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="menu:wallet"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Top-up crypto selection ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("topup_crypto:"))
async def handle_topup_crypto(
    callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"
):
    parts = callback.data.split(":")
    amount_str = parts[1].replace("_", ".")
    currency_str = parts[2]

    try:
        amount = float(amount_str)
        currency = CryptoCurrency(currency_str)
    except (ValueError, KeyError):
        await callback.answer("Invalid data.", show_alert=True)
        return

    # Create a Payment record flagged as wallet deposit (no order)
    wallet_address = CRYPTO_ADDRESSES.get(currency, "")
    payment = Payment(
        payment_reference=generate_payment_reference(),
        user_telegram_id=callback.from_user.id,
        amount_usdt=amount,
        currency=currency,
        wallet_address=wallet_address,
        status=PaymentStatus.PENDING,
        is_wallet_deposit=True,
    )
    session.add(payment)
    await session.flush()
    await session.commit()

    network_name = CRYPTO_NETWORK_NAMES.get(currency, currency.value)
    text = get_text(
        "wallet_topup_details", user_lang,
        amount=format_price(amount),
        network=network_name,
        address=wallet_address,
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=get_text("btn_submit_deposit", user_lang),
            callback_data=f"topup_txid:{payment.id}",
        )],
        [InlineKeyboardButton(text=get_text("btn_home", user_lang), callback_data="menu:home")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

    try:
        qr = generate_qr_code(wallet_address)
        await callback.message.answer_photo(
            photo=qr,
            caption=f"📲 QR — {network_name}\n\n<code>{wallet_address}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Deposit QR failed: {e}")

    await callback.answer()


# ─── Top-up TXID submission ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("topup_txid:"))
async def handle_topup_txid_prompt(
    callback: CallbackQuery, state: FSMContext, user_lang: str = "en"
):
    payment_id = int(callback.data.split(":")[1])
    await state.set_state(WalletTopUpStates.waiting_for_txid)
    await state.update_data(deposit_payment_id=payment_id)
    await callback.message.answer(get_text("submit_txid", user_lang), parse_mode="HTML")
    await callback.answer()


@router.message(WalletTopUpStates.waiting_for_txid)
async def handle_topup_txid_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user_lang: str = "en",
):
    data = await state.get_data()
    payment_id = data.get("deposit_payment_id")
    txid = message.text.strip() if message.text else ""

    if not txid or len(txid) < 10:
        await message.answer("⚠️ Invalid TXID. Please send a valid transaction ID or link.")
        return

    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        await message.answer("❌ Payment record not found.")
        await state.clear()
        return

    # IDOR guard — only the payment owner may submit TXID
    if payment.user_telegram_id != message.from_user.id:
        await message.answer("❌ Unauthorized.")
        await state.clear()
        return

    if txid.startswith("http"):
        payment.transaction_link = txid
    else:
        payment.txid = txid
    payment.status = PaymentStatus.SUBMITTED
    await session.commit()
    await state.clear()

    text = get_text("wallet_topup_received", user_lang, amount=format_price(payment.amount_usdt))
    kb = get_back_keyboard(user_lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

    # Notify admins
    admin_text = (
        f"💰 <b>Wallet Deposit Request</b>\n\n"
        f"👤 User: <code>{message.from_user.id}</code> (@{message.from_user.username or 'N/A'})\n"
        f"💵 Amount: <b>${payment.amount_usdt:.2f} USDT</b>\n"
        f"🌐 Network: <b>{payment.currency.value}</b>\n"
        f"📋 TXID: <code>{txid}</code>"
    )
    deposit_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Credit Wallet", callback_data=f"admin_confirm_deposit:{payment_id}"
        ),
        InlineKeyboardButton(
            text="❌ Reject Deposit", callback_data=f"admin_reject_deposit:{payment_id}"
        ),
    ]])
    try:
        notif = NotificationService(message.bot)
        await notif.notify_admins(settings.admin_list, admin_text, deposit_kb)
    except Exception as e:
        logger.error(f"Deposit admin notify failed: {e}")


# ─── Admin: confirm / reject wallet deposit ─────────────────────────────────────

@router.callback_query(F.data.startswith("admin_confirm_deposit:"))
async def handle_admin_confirm_deposit(
    callback: CallbackQuery, session: AsyncSession
):
    from bot.utils.admin import is_admin
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized.", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    # Row-lock the payment to prevent double-credit by concurrent admin clicks
    result = await session.execute(
        select(Payment)
        .where(Payment.id == payment_id)
        .with_for_update()
    )
    payment = result.scalar_one_or_none()

    if not payment or not payment.is_wallet_deposit:
        await callback.answer("Payment not found or not a deposit.", show_alert=True)
        return
    if payment.status != PaymentStatus.SUBMITTED:
        await callback.answer("Already processed.", show_alert=True)
        return

    # Atomic status transition SUBMITTED → CONFIRMED
    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_by_admin = callback.from_user.id

    wallet_svc = WalletService(session)
    credited = await wallet_svc.credit(
        user_telegram_id=payment.user_telegram_id,
        amount=payment.amount_usdt,
        tx_type=TransactionType.DEPOSIT,
        reference_id=payment.payment_reference,
        description=f"Wallet top-up via {payment.currency.value}",
    )
    await session.commit()

    if credited:
        new_balance = await wallet_svc.get_balance(payment.user_telegram_id)
        user_text = get_text(
            "wallet_topup_credited",
            "en",  # We don't have the user's lang here easily; keep English for now
            amount=format_price(payment.amount_usdt),
            balance=format_price(new_balance),
        )
        try:
            notif = NotificationService(callback.bot)
            await notif.notify_user(payment.user_telegram_id, user_text)
        except Exception as e:
            logger.error(f"Deposit confirmation notify failed: {e}")

    try:
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ <b>DEPOSIT CONFIRMED — WALLET CREDITED</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer("✅ Wallet credited!", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_deposit:"))
async def handle_admin_reject_deposit(
    callback: CallbackQuery, session: AsyncSession
):
    from bot.utils.admin import is_admin
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized.", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        await callback.answer("Payment not found.", show_alert=True)
        return
    if payment.status in (PaymentStatus.CONFIRMED, PaymentStatus.REJECTED):
        await callback.answer("Already processed.", show_alert=True)
        return

    payment.status = PaymentStatus.REJECTED
    payment.confirmed_by_admin = callback.from_user.id
    await session.commit()

    user_text = get_text(
        "wallet_topup_rejected", "en",
        amount=format_price(payment.amount_usdt),
    )
    try:
        notif = NotificationService(callback.bot)
        await notif.notify_user(payment.user_telegram_id, user_text)
    except Exception as e:
        logger.error(f"Deposit rejection notify failed: {e}")

    try:
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ <b>DEPOSIT REJECTED</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer("❌ Deposit rejected.", show_alert=True)


# ─── Pay from wallet ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("wallet_pay:"))
async def handle_pay_from_wallet(
    callback: CallbackQuery, session: AsyncSession, user_lang: str = "en"
):
    product_id = int(callback.data.split(":")[1])

    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product or not product.is_active or product.quantity <= 0:
        await callback.answer(get_text("out_of_stock", user_lang), show_alert=True)
        return

    wallet_svc = WalletService(session)
    balance = await wallet_svc.get_balance(callback.from_user.id)

    if balance < product.price_usdt:
        text = get_text(
            "wallet_insufficient", user_lang,
            balance=format_price(balance),
            required=format_price(product.price_usdt),
        )
        await callback.answer(text, show_alert=True)
        return

    # Create order
    order_svc = OrderService(session)
    order = await order_svc.create_order(
        user_telegram_id=callback.from_user.id,
        product_id=product_id,
    )
    if not order:
        await callback.answer("❌ Failed to create order.", show_alert=True)
        return

    # Atomically debit wallet (row-locked)
    debited = await wallet_svc.debit(
        user_telegram_id=callback.from_user.id,
        amount=order.final_price,
        tx_type=TransactionType.PURCHASE,
        reference_id=order.order_number,
        description=f"Purchase: {product.get_name(user_lang)}",
    )
    if not debited:
        # Not enough balance — cancel the order and abort
        order.status = OrderStatus.CANCELLED
        await session.commit()
        await callback.answer(get_text("wallet_insufficient", user_lang,
                                       balance=format_price(balance),
                                       required=format_price(order.final_price)), show_alert=True)
        return

    order.status = OrderStatus.PREPARING
    await session.flush()

    # Try to deliver
    delivery_svc = DeliveryService(session)
    content = await delivery_svc.deliver_order(order.id)

    if not content:
        # No stock — roll back everything (debit + order creation)
        await session.rollback()
        await callback.answer(get_text("out_of_stock", user_lang), show_alert=True)
        return

    # Delivery succeeded — update user stats then commit once
    user_res = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user_obj = user_res.scalar_one_or_none()
    if user_obj:
        user_obj.total_orders += 1
        user_obj.total_spent += order.final_price
        await session.flush()

    await session.commit()

    new_balance = await wallet_svc.get_balance(callback.from_user.id)
    success_text = get_text(
        "wallet_pay_success", user_lang,
        amount=format_price(order.final_price),
        balance=format_price(new_balance),
    )
    delivery_text = get_text(
        "order_delivered", user_lang,
        order_number=order.order_number,
        content=content,
    )

    kb = get_back_keyboard(user_lang)
    try:
        await callback.message.edit_text(
            success_text + "\n\n" + delivery_text,
            reply_markup=kb,
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(success_text, reply_markup=kb, parse_mode="HTML")
        await callback.message.answer(delivery_text, parse_mode="HTML")

    await callback.answer()
