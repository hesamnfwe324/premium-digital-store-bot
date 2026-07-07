from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import (
    Payment, PaymentStatus, CryptoCurrency,
    CRYPTO_NETWORK_NAMES, CRYPTO_EMOJIS,
)
from bot.services.payment_service import CRYPTO_ADDRESSES
from bot.keyboards.vps import (
    get_vps_type_keyboard,
    get_vps_location_keyboard,
    get_vps_plan_keyboard,
    get_vps_gpu_keyboard,
    get_vps_duration_keyboard,
    get_vps_os_keyboard,
    get_vps_confirm_keyboard,
    get_vps_crypto_keyboard,
    get_vps_payment_admin_keyboard,
    get_vps_ordered_keyboard,
    get_location_by_id,
    get_plan_by_id,
    get_gpu_by_id,
    get_duration_by_id,
    get_os_by_id,
    calculate_total,
)
from bot.utils.i18n import get_text
from bot.utils.helpers import generate_payment_reference
from bot.utils.qr_code import generate_qr_code
from bot.utils.logger import logger
from config import settings

router = Router()


class VpsPaymentStates(StatesGroup):
    waiting_for_txid = State()


# ─── Small helpers ─────────────────────────────────────────────────────────────

def _loc_name(loc: dict, lang: str) -> str:
    return loc.get("name_fa" if lang == "fa" else "name_en", "")

def _gpu_name(gpu: dict, lang: str) -> str:
    return gpu.get("name_fa" if lang == "fa" else "name_en", "")

def _dur_name(dur: dict, lang: str) -> str:
    return dur.get("name_fa" if lang == "fa" else "name_en", "")

def _plan_specs_text(plan: dict, lang: str) -> str:
    use_case = plan.get("use_case_fa" if lang == "fa" else "use_case_en", "")
    return (
        f"🖥 CPU: <code>{plan.get('cpu','')}</code>\n"
        f"💾 RAM: <code>{plan.get('ram','')}</code>\n"
        f"💿 Disk: <code>{plan.get('disk','')}</code>\n"
        f"🌐 Bandwidth: <code>{plan.get('bandwidth','')}</code>\n"
        f"⚡ Network: <code>{plan.get('network','')}</code>\n"
        f"💡 <i>{use_case}</i>"
    )

async def _edit_or_send(callback: CallbackQuery, text: str, kb):
    """Edit existing message or send new one if edit fails."""
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 0 — Menu entry (wide button in main menu)
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:vps")
async def handle_vps_menu(callback: CallbackQuery, user_lang: str = "en"):
    await _edit_or_send(callback, get_text("vps_menu_title", user_lang), get_vps_type_keyboard(user_lang))
    await callback.answer()


@router.callback_query(F.data == "vps:start")
async def handle_vps_start(callback: CallbackQuery, user_lang: str = "en"):
    """Back from Location → Type keyboard."""
    await _edit_or_send(callback, get_text("vps_menu_title", user_lang), get_vps_type_keyboard(user_lang))
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Type selected → Location keyboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps:type:"))
async def handle_vps_type(callback: CallbackQuery, user_lang: str = "en"):
    server_type = callback.data.split(":")[2]   # "virtual" | "dedicated"
    await _edit_or_send(
        callback,
        get_text("vps_select_location", user_lang),
        get_vps_location_keyboard(server_type, user_lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vps:back:loc:"))
async def handle_vps_back_to_location(callback: CallbackQuery, user_lang: str = "en"):
    """Back from Plan list → Location keyboard.  data = vps:back:loc:{type}"""
    server_type = callback.data.split(":")[3]
    await _edit_or_send(
        callback,
        get_text("vps_select_location", user_lang),
        get_vps_location_keyboard(server_type, user_lang)
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Location selected → Plan keyboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps:loc:"))
async def handle_vps_location(callback: CallbackQuery, user_lang: str = "en"):
    """vps:loc:{type}:{loc_id}  — also used as back-target from GPU keyboard."""
    parts = callback.data.split(":")
    server_type, location_id = parts[2], parts[3]

    loc      = get_location_by_id(location_id)
    flag     = loc.get("flag", "🌍")
    loc_name = _loc_name(loc, user_lang)

    dc_info = get_text("vps_datacenter_info", user_lang, flag=flag, location=loc_name)
    text = get_text("vps_select_plan", user_lang) + f"\n\n{dc_info}"

    await _edit_or_send(callback, text, get_vps_plan_keyboard(server_type, location_id, user_lang))
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Plan selected → GPU keyboard (if GPU-capable) or Duration keyboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps:plan:"))
async def handle_vps_plan(callback: CallbackQuery, user_lang: str = "en"):
    """vps:plan:{type}:{loc}:{plan_id}  — also used as back-target from Duration."""
    parts = callback.data.split(":")
    server_type, location_id, plan_id = parts[2], parts[3], parts[4]

    plan  = get_plan_by_id(plan_id)
    specs = _plan_specs_text(plan, user_lang)

    if plan.get("gpu_support"):
        text = get_text("vps_select_gpu", user_lang) + f"\n\n<b>{plan.get('name','')}</b>\n{specs}"
        kb   = get_vps_gpu_keyboard(server_type, location_id, plan_id, user_lang)
    else:
        text = get_text("vps_select_duration", user_lang) + f"\n\n<b>{plan.get('name','')}</b>\n{specs}"
        kb   = get_vps_duration_keyboard(server_type, location_id, plan_id, "no_gpu", user_lang)

    await _edit_or_send(callback, text, kb)
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — GPU selected → Duration keyboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps:gpu:"))
async def handle_vps_gpu(callback: CallbackQuery, user_lang: str = "en"):
    """vps:gpu:{type}:{loc}:{plan_id}:{gpu_id}"""
    parts = callback.data.split(":")
    server_type, location_id, plan_id, gpu_id = parts[2], parts[3], parts[4], parts[5]

    plan = get_plan_by_id(plan_id)
    gpu  = get_gpu_by_id(gpu_id)

    text = (
        get_text("vps_select_duration", user_lang)
        + f"\n\n<b>{plan.get('name','')}</b>\n"
        + _plan_specs_text(plan, user_lang)
        + f"\n🎮 GPU: <b>{_gpu_name(gpu, user_lang)}</b>"
    )
    await _edit_or_send(callback, text, get_vps_duration_keyboard(server_type, location_id, plan_id, gpu_id, user_lang))
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Duration selected → OS keyboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps:dur:"))
async def handle_vps_duration(callback: CallbackQuery, user_lang: str = "en"):
    """vps:dur:{type}:{loc}:{plan}:{gpu}:{dur_id}"""
    parts = callback.data.split(":")
    server_type, location_id, plan_id, gpu_id, dur_id = parts[2], parts[3], parts[4], parts[5], parts[6]

    plan  = get_plan_by_id(plan_id)
    gpu   = get_gpu_by_id(gpu_id)
    dur   = get_duration_by_id(dur_id)
    total = calculate_total(plan, gpu, dur)

    text = (
        get_text("vps_select_os", user_lang)
        + f"\n\n<b>{plan.get('name','')}</b>"
        + f"\n📅 {_dur_name(dur, user_lang)}  —  <b>${total:.2f} USDT total</b>"
    )
    await _edit_or_send(callback, text, get_vps_os_keyboard(server_type, location_id, plan_id, gpu_id, dur_id, user_lang))
    await callback.answer()


# BACK from OS keyboard → Duration keyboard
@router.callback_query(F.data.startswith("vps:showdur:"))
async def handle_vps_show_duration(callback: CallbackQuery, user_lang: str = "en"):
    """vps:showdur:{type}:{loc}:{plan}:{gpu}  — back from OS keyboard"""
    parts = callback.data.split(":")
    server_type, location_id, plan_id, gpu_id = parts[2], parts[3], parts[4], parts[5]

    plan  = get_plan_by_id(plan_id)
    specs = _plan_specs_text(plan, user_lang)

    text = (
        get_text("vps_select_duration", user_lang)
        + f"\n\n<b>{plan.get('name','')}</b>\n{specs}"
    )
    if gpu_id != "no_gpu":
        gpu = get_gpu_by_id(gpu_id)
        text += f"\n🎮 GPU: <b>{_gpu_name(gpu, user_lang)}</b>"

    await _edit_or_send(callback, text, get_vps_duration_keyboard(server_type, location_id, plan_id, gpu_id, user_lang))
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — OS selected → Order Summary
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps:os:"))
async def handle_vps_os(callback: CallbackQuery, user_lang: str = "en"):
    """vps:os:{type}:{loc}:{plan}:{gpu}:{dur}:{os_id}"""
    parts = callback.data.split(":")
    server_type, location_id, plan_id, gpu_id, dur_id, os_id = (
        parts[2], parts[3], parts[4], parts[5], parts[6], parts[7]
    )

    loc    = get_location_by_id(location_id)
    plan   = get_plan_by_id(plan_id)
    gpu    = get_gpu_by_id(gpu_id)
    dur    = get_duration_by_id(dur_id)
    os_opt = get_os_by_id(os_id)
    total  = calculate_total(plan, gpu, dur)

    flag       = loc.get("flag", "🌍")
    loc_name   = _loc_name(loc, user_lang)
    gpu_name   = _gpu_name(gpu, user_lang)
    dur_name   = _dur_name(dur, user_lang)
    type_label = "Virtual (VPS/VDS)" if server_type == "virtual" else "Dedicated Server"

    text = get_text(
        "vps_order_summary", user_lang,
        type=type_label,
        location=f"{flag} {loc_name}",
        cpu=plan.get("cpu", ""),
        ram=plan.get("ram", ""),
        disk=plan.get("disk", ""),
        bandwidth=plan.get("bandwidth", ""),
        network=plan.get("network", ""),
        gpu=gpu_name,
        duration=dur_name,
        os=os_opt.get("name", os_id),
        total=f"{total:.2f}",
    )
    kb = get_vps_confirm_keyboard(server_type, location_id, plan_id, gpu_id, dur_id, os_id, user_lang)
    await _edit_or_send(callback, text, kb)
    await callback.answer()


# BACK from Confirm (summary) → OS keyboard
@router.callback_query(F.data.startswith("vps:showos:"))
async def handle_vps_show_os(callback: CallbackQuery, user_lang: str = "en"):
    """vps:showos:{type}:{loc}:{plan}:{gpu}:{dur}  — back from Confirm page"""
    parts = callback.data.split(":")
    server_type, location_id, plan_id, gpu_id, dur_id = (
        parts[2], parts[3], parts[4], parts[5], parts[6]
    )

    plan  = get_plan_by_id(plan_id)
    gpu   = get_gpu_by_id(gpu_id)
    dur   = get_duration_by_id(dur_id)
    total = calculate_total(plan, gpu, dur)

    text = (
        get_text("vps_select_os", user_lang)
        + f"\n\n<b>{plan.get('name','')}</b>"
        + f"\n📅 {_dur_name(dur, user_lang)}  —  <b>${total:.2f} USDT total</b>"
    )
    await _edit_or_send(callback, text, get_vps_os_keyboard(server_type, location_id, plan_id, gpu_id, dur_id, user_lang))
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Confirm → Crypto selection (store order in FSM)
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps:confirm:"))
async def handle_vps_confirm(callback: CallbackQuery, state: FSMContext, user_lang: str = "en"):
    """vps:confirm:{type}:{loc}:{plan}:{gpu}:{dur}:{os}"""
    parts = callback.data.split(":")
    server_type, location_id, plan_id, gpu_id, dur_id, os_id = (
        parts[2], parts[3], parts[4], parts[5], parts[6], parts[7]
    )

    loc    = get_location_by_id(location_id)
    plan   = get_plan_by_id(plan_id)
    gpu    = get_gpu_by_id(gpu_id)
    dur    = get_duration_by_id(dur_id)
    os_opt = get_os_by_id(os_id)
    total  = calculate_total(plan, gpu, dur)

    flag       = loc.get("flag", "🌍")
    loc_name   = _loc_name(loc, user_lang)
    gpu_name   = _gpu_name(gpu, user_lang)
    dur_name   = _dur_name(dur, user_lang)
    type_label = "Virtual (VPS/VDS)" if server_type == "virtual" else "Dedicated Server"

    # Persist order details in FSM — used during payment steps
    await state.update_data(
        server_type=server_type, location_id=location_id,
        plan_id=plan_id, gpu_id=gpu_id, dur_id=dur_id, os_id=os_id,
        total=total,
        type_label=type_label,
        loc_name=f"{flag} {loc_name}",
        plan_name=plan.get("name", ""),
        cpu=plan.get("cpu", ""),
        ram=plan.get("ram", ""),
        disk=plan.get("disk", ""),
        bandwidth=plan.get("bandwidth", ""),
        network=plan.get("network", ""),
        gpu_name=gpu_name,
        dur_name=dur_name,
        os_name=os_opt.get("name", os_id),
        user_lang=user_lang,
    )

    text = get_text("vps_select_crypto", user_lang, total=f"{total:.2f}")
    await _edit_or_send(callback, text, get_vps_crypto_keyboard(user_lang))
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Crypto selected → Show address + QR
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps_pay:"))
async def handle_vps_pay_crypto(callback: CallbackQuery, state: FSMContext, user_lang: str = "en"):
    """vps_pay:{currency_value}"""
    currency_value = callback.data.split(":")[1]

    try:
        currency = CryptoCurrency(currency_value)
    except ValueError:
        await callback.answer("❌ Invalid currency", show_alert=True)
        return

    data = await state.get_data()
    if not data.get("total"):
        await callback.answer(get_text("vps_session_expired", user_lang), show_alert=True)
        return

    total   = data["total"]
    address = CRYPTO_ADDRESSES.get(currency, "")
    if not address:
        await callback.answer("❌ This currency is temporarily unavailable. Please choose another.", show_alert=True)
        return

    emoji    = CRYPTO_EMOJIS.get(currency, "💰")
    net_name = CRYPTO_NETWORK_NAMES.get(currency, currency_value)

    # Store payment choice in FSM and set state
    await state.update_data(currency_value=currency_value, wallet_address=address)
    await state.set_state(VpsPaymentStates.waiting_for_txid)

    text = get_text(
        "vps_payment_instruction", user_lang,
        emoji=emoji, network=net_name,
        amount=f"{total:.2f}", address=address,
    )

    try:
        qr_bytes = await generate_qr_code(address)
        await callback.message.answer_photo(qr_bytes, caption=text, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")

    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — TXID received → Create DB payment record, notify admins
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(VpsPaymentStates.waiting_for_txid)
async def handle_vps_txid(message: Message, state: FSMContext, session: AsyncSession, user_lang: str = "en"):
    txid = (message.text or "").strip()
    if not txid:
        await message.answer(get_text("vps_txid_invalid", user_lang))
        return

    data           = await state.get_data()
    total          = data.get("total", 0)
    currency_value = data.get("currency_value", "")
    address        = data.get("wallet_address", "")
    lang           = data.get("user_lang", user_lang)

    try:
        currency = CryptoCurrency(currency_value)
    except ValueError:
        currency = None

    # Create Payment record in DB (no order FK — VPS orders are manual)
    payment_ref = generate_payment_reference()
    payment_id  = None
    try:
        payment = Payment(
            payment_reference=payment_ref,
            user_telegram_id=message.from_user.id,
            amount_usdt=float(total),
            currency=currency,
            wallet_address=address,
            status=PaymentStatus.SUBMITTED,
        )
        if txid.startswith("http"):
            payment.transaction_link = txid
        else:
            payment.txid = txid
        session.add(payment)
        await session.commit()
        payment_id = payment.id
    except Exception as exc:
        logger.error(f"VPS payment DB error: {exc}")

    # Build detailed admin notification
    emoji    = CRYPTO_EMOJIS.get(currency, "💰") if currency else "💰"
    net_name = CRYPTO_NETWORK_NAMES.get(currency, currency_value) if currency else currency_value

    admin_msg = (
        f"🖥 <b>New VPS Order — Payment Submitted</b>\n\n"
        f"👤 User: <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> "
        f"(<code>{message.from_user.id}</code>)\n\n"
        f"<b>📋 Order Details:</b>\n"
        f"🖥 Type: <b>{data.get('type_label','')}</b>\n"
        f"📍 Location: <b>{data.get('loc_name','')}</b>\n"
        f"📦 Plan: <b>{data.get('plan_name','')}</b>\n"
        f"🖥 CPU: <code>{data.get('cpu','')}</code>\n"
        f"💾 RAM: <code>{data.get('ram','')}</code>\n"
        f"💿 Disk: <code>{data.get('disk','')}</code>\n"
        f"🌐 Bandwidth: <code>{data.get('bandwidth','')}</code>\n"
        f"⚡ Network: <code>{data.get('network','')}</code>\n"
        f"🎮 GPU: <b>{data.get('gpu_name','')}</b>\n"
        f"📅 Duration: <b>{data.get('dur_name','')}</b>\n"
        f"💻 OS: <b>{data.get('os_name','')}</b>\n\n"
        f"<b>💳 Payment:</b>\n"
        f"{emoji} Network: <b>{net_name}</b>\n"
        f"💰 Amount: <b>${total:.2f} USDT</b>\n"
        f"🔑 TXID/Link: <code>{txid}</code>\n"
        f"🧾 Ref: <code>{payment_ref}</code>"
    )

    kb_admin = get_vps_payment_admin_keyboard(payment_id) if payment_id else None
    for admin_id in settings.ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, admin_msg, parse_mode="HTML", reply_markup=kb_admin)
        except Exception as exc:
            logger.warning(f"Could not notify admin {admin_id}: {exc}")

    await state.clear()

    # Confirm to user
    text    = get_text("vps_payment_submitted", lang, ref=payment_ref, total=f"{total:.2f}")
    kb_user = get_vps_ordered_keyboard(lang)
    await message.answer(text, reply_markup=kb_user, parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN — Confirm / Reject VPS payment
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("vps_confirm_pay:"))
async def handle_admin_vps_confirm(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    result     = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment    = result.scalar_one_or_none()

    if not payment:
        await callback.answer("❌ Payment record not found.", show_alert=True)
        return

    from datetime import datetime, timezone
    payment.status            = PaymentStatus.CONFIRMED
    payment.confirmed_by_admin = callback.from_user.id
    payment.confirmed_at      = datetime.now(timezone.utc)
    await session.commit()

    try:
        await callback.bot.send_message(
            payment.user_telegram_id,
            "✅ <b>Payment Confirmed!</b>\n\n"
            f"💰 <b>${payment.amount_usdt:.2f} USDT</b> has been verified.\n\n"
            "🖥 Your server is being set up now.\n"
            "⏱ Estimated time: <b>1–4 hours</b>\n\n"
            "You will receive your login credentials here once the server is ready.\n"
            "For questions, tap Support below.",
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning(f"Could not notify VPS customer: {exc}")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ Confirmed & customer notified!", show_alert=True)


@router.callback_query(F.data.startswith("vps_reject_pay:"))
async def handle_admin_vps_reject(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("⛔ Unauthorized", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    result     = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment    = result.scalar_one_or_none()

    if not payment:
        await callback.answer("❌ Payment record not found.", show_alert=True)
        return

    payment.status = PaymentStatus.REJECTED
    await session.commit()

    try:
        await callback.bot.send_message(
            payment.user_telegram_id,
            "❌ <b>Payment Not Verified</b>\n\n"
            "We could not confirm your VPS payment.\n\n"
            "Please double-check the transaction and try again, "
            "or contact support for assistance.",
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning(f"Could not notify VPS customer on reject: {exc}")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("❌ Rejected & customer notified.", show_alert=True)
