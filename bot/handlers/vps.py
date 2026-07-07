from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.keyboards.vps import (
    get_vps_type_keyboard,
    get_vps_location_keyboard,
    get_vps_plan_keyboard,
    get_vps_gpu_keyboard,
    get_vps_duration_keyboard,
    get_vps_os_keyboard,
    get_vps_confirm_keyboard,
    get_vps_ordered_keyboard,
    get_location_by_id,
    get_plan_by_id,
    get_gpu_by_id,
    get_duration_by_id,
    get_os_by_id,
    calculate_total,
    DEDICATED_PLANS,
)
from bot.utils.i18n import get_text

router = Router()


def _loc_name(loc: dict, lang: str) -> str:
    return loc.get("name_fa" if lang == "fa" else "name_en", "")


def _gpu_name(gpu: dict, lang: str) -> str:
    return gpu.get("name_fa" if lang == "fa" else "name_en", "")


def _dur_name(dur: dict, lang: str) -> str:
    return dur.get("name_fa" if lang == "fa" else "name_en", "")


# ─── Main VPS entry (menu button) ────────────────────────────────────────────

@router.callback_query(F.data == "menu:vps")
async def handle_vps_menu(callback: CallbackQuery, user_lang: str = "en"):
    text = get_text("vps_menu_title", user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=get_vps_type_keyboard(user_lang), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=get_vps_type_keyboard(user_lang), parse_mode="HTML")
    await callback.answer()


# back to VPS type selection
@router.callback_query(F.data == "vps:start")
async def handle_vps_start(callback: CallbackQuery, user_lang: str = "en"):
    text = get_text("vps_menu_title", user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=get_vps_type_keyboard(user_lang), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=get_vps_type_keyboard(user_lang), parse_mode="HTML")
    await callback.answer()


# ─── Type selected → Location ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vps:type:"))
async def handle_vps_type(callback: CallbackQuery, user_lang: str = "en"):
    server_type = callback.data.split(":")[2]  # virtual | dedicated
    text = get_text("vps_select_location", user_lang)
    try:
        await callback.message.edit_text(
            text, reply_markup=get_vps_location_keyboard(server_type, user_lang), parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text, reply_markup=get_vps_location_keyboard(server_type, user_lang), parse_mode="HTML"
        )
    await callback.answer()


# back to location from plan/etc
@router.callback_query(F.data.startswith("vps:location:"))
async def handle_vps_back_to_location(callback: CallbackQuery, user_lang: str = "en"):
    server_type = callback.data.split(":")[2]
    text = get_text("vps_select_location", user_lang)
    try:
        await callback.message.edit_text(
            text, reply_markup=get_vps_location_keyboard(server_type, user_lang), parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text, reply_markup=get_vps_location_keyboard(server_type, user_lang), parse_mode="HTML"
        )
    await callback.answer()


# ─── Location selected → Plan ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vps:loc:"))
async def handle_vps_location(callback: CallbackQuery, user_lang: str = "en"):
    # vps:loc:{type}:{loc_id}
    parts = callback.data.split(":")
    server_type = parts[2]
    location_id = parts[3]

    loc = get_location_by_id(location_id)
    loc_name = _loc_name(loc, user_lang)
    flag = loc.get("flag", "🌍")

    dc_info = get_text("vps_datacenter_info", user_lang, flag=flag, location=loc_name)
    text = get_text("vps_select_plan", user_lang) + f"\n\n{dc_info}"
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_vps_plan_keyboard(server_type, location_id, user_lang),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=get_vps_plan_keyboard(server_type, location_id, user_lang),
            parse_mode="HTML",
        )
    await callback.answer()


# ─── Plan selected → GPU (dedicated) or Duration (virtual) ───────────────────

@router.callback_query(F.data.startswith("vps:plan:"))
async def handle_vps_plan(callback: CallbackQuery, user_lang: str = "en"):
    # vps:plan:{type}:{loc}:{plan_id}
    parts = callback.data.split(":")
    server_type = parts[2]
    location_id = parts[3]
    plan_id = parts[4]

    plan = get_plan_by_id(plan_id, server_type)

    # Build spec text
    spec_lines = [
        f"<b>{plan.get('name', '')}</b>",
        f"🖥 CPU: <code>{plan.get('cpu', '')}</code>",
        f"💾 RAM: <code>{plan.get('ram', '')}</code>",
        f"💿 Disk: <code>{plan.get('disk', '')}</code>",
        f"🌐 Bandwidth: <code>{plan.get('bandwidth', '')}</code>",
        f"💵 Base: <b>${plan.get('price', 0):.0f}/month</b>",
    ]
    spec_text = "\n".join(spec_lines)

    # Dedicated plans with GPU support → show GPU selection
    if server_type == "dedicated" and plan.get("gpu_support", False):
        text = get_text("vps_select_gpu", user_lang) + f"\n\n{spec_text}"
        kb = get_vps_gpu_keyboard(server_type, location_id, plan_id, user_lang)
    else:
        # No GPU → go to duration
        gpu_id = "no_gpu"
        text = get_text("vps_select_duration", user_lang) + f"\n\n{spec_text}"
        kb = get_vps_duration_keyboard(server_type, location_id, plan_id, gpu_id, user_lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─── GPU selected → Duration ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vps:gpu:"))
async def handle_vps_gpu(callback: CallbackQuery, user_lang: str = "en"):
    # vps:gpu:{type}:{loc}:{plan_id}:{gpu_id}
    parts = callback.data.split(":")
    server_type = parts[2]
    location_id = parts[3]
    plan_id = parts[4]
    gpu_id = parts[5]

    gpu = get_gpu_by_id(gpu_id)
    gpu_name = _gpu_name(gpu, user_lang)
    plan = get_plan_by_id(plan_id, server_type)

    extra_cost = gpu.get("extra", 0)
    new_base = plan.get("price", 0) + extra_cost

    text = (
        get_text("vps_select_duration", user_lang)
        + f"\n\n🎮 GPU: <b>{gpu_name}</b>"
        + (f" <i>(+${extra_cost}/mo)</i>" if extra_cost else "")
        + f"\n💵 New base: <b>${new_base:.0f}/month</b>"
    )
    kb = get_vps_duration_keyboard(server_type, location_id, plan_id, gpu_id, user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─── Duration selected → OS ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vps:dur:"))
async def handle_vps_duration(callback: CallbackQuery, user_lang: str = "en"):
    # vps:dur:{type}:{loc}:{plan}:{gpu}:{dur_id}
    parts = callback.data.split(":")
    server_type = parts[2]
    location_id = parts[3]
    plan_id = parts[4]
    gpu_id = parts[5]
    duration_id = parts[6]

    dur = get_duration_by_id(duration_id)
    dur_name = _dur_name(dur, user_lang)
    plan = get_plan_by_id(plan_id, server_type)
    gpu = get_gpu_by_id(gpu_id)
    total = calculate_total(plan, gpu, dur)

    text = (
        get_text("vps_select_os", user_lang)
        + f"\n\n📅 {get_text('vps_duration_label', user_lang)}: <b>{dur_name}</b>"
        + f"\n💰 {get_text('vps_total_label', user_lang)}: <b>${total:.2f}</b>"
    )
    kb = get_vps_os_keyboard(server_type, location_id, plan_id, gpu_id, duration_id, user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─── OS selected → Summary/Confirm ───────────────────────────────────────────

@router.callback_query(F.data.startswith("vps:os:"))
async def handle_vps_os(callback: CallbackQuery, user_lang: str = "en"):
    # vps:os:{type}:{loc}:{plan}:{gpu}:{dur}:{os_id}
    parts = callback.data.split(":")
    server_type = parts[2]
    location_id = parts[3]
    plan_id = parts[4]
    gpu_id = parts[5]
    duration_id = parts[6]
    os_id = parts[7]

    plan = get_plan_by_id(plan_id, server_type)
    gpu = get_gpu_by_id(gpu_id)
    dur = get_duration_by_id(duration_id)
    loc = get_location_by_id(location_id)
    os_opt = get_os_by_id(os_id)

    total = calculate_total(plan, gpu, dur)
    gpu_name = _gpu_name(gpu, user_lang)
    dur_name = _dur_name(dur, user_lang)
    loc_name = _loc_name(loc, user_lang)
    flag = loc.get("flag", "🌍")
    type_label = get_text("btn_vps_dedicated" if server_type == "dedicated" else "btn_vps_virtual", user_lang)

    summary = get_text(
        "vps_order_summary",
        user_lang,
        type=type_label,
        location=f"{flag} {loc_name}",
        plan=plan.get("name", ""),
        cpu=plan.get("cpu", ""),
        ram=plan.get("ram", ""),
        disk=plan.get("disk", ""),
        bandwidth=plan.get("bandwidth", ""),
        gpu=gpu_name,
        duration=dur_name,
        os=os_opt.get("name", os_id),
        total=f"{total:.2f}",
    )

    kb = get_vps_confirm_keyboard(server_type, location_id, plan_id, gpu_id, duration_id, os_id, user_lang)
    try:
        await callback.message.edit_text(summary, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(summary, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─── Confirm order ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vps:confirm:"))
async def handle_vps_confirm(callback: CallbackQuery, user_lang: str = "en"):
    # vps:confirm:{type}:{loc}:{plan}:{gpu}:{dur}:{os}
    parts = callback.data.split(":")
    server_type = parts[2]
    location_id = parts[3]
    plan_id = parts[4]
    gpu_id = parts[5]
    duration_id = parts[6]
    os_id = parts[7]

    plan = get_plan_by_id(plan_id, server_type)
    gpu = get_gpu_by_id(gpu_id)
    dur = get_duration_by_id(duration_id)
    loc = get_location_by_id(location_id)
    os_opt = get_os_by_id(os_id)
    total = calculate_total(plan, gpu, dur)
    dur_name = _dur_name(dur, user_lang)
    loc_name = _loc_name(loc, user_lang)
    flag = loc.get("flag", "🌍")
    gpu_name = _gpu_name(gpu, user_lang)

    # Notify admins
    try:
        from config import settings
        admin_msg = (
            f"🖥 <b>New VPS Order Request</b>\n\n"
            f"👤 User: <a href='tg://user?id={callback.from_user.id}'>{callback.from_user.full_name}</a> "
            f"(<code>{callback.from_user.id}</code>)\n"
            f"🌐 Type: <b>{'Dedicated' if server_type == 'dedicated' else 'Virtual'}</b>\n"
            f"📍 Location: <b>{flag} {loc_name}</b>\n"
            f"📦 Plan: <b>{plan.get('name', '')}</b>\n"
            f"🖥 CPU: <code>{plan.get('cpu', '')}</code>\n"
            f"💾 RAM: <code>{plan.get('ram', '')}</code>\n"
            f"💿 Disk: <code>{plan.get('disk', '')}</code>\n"
            f"🎮 GPU: <b>{gpu_name}</b>\n"
            f"📅 Duration: <b>{dur_name}</b>\n"
            f"💻 OS: <b>{os_opt.get('name', os_id)}</b>\n"
            f"💰 <b>Total: ${total:.2f} USDT</b>"
        )
        for admin_id in settings.ADMIN_IDS:
            try:
                await callback.bot.send_message(admin_id, admin_msg, parse_mode="HTML")
            except Exception:
                pass
    except Exception:
        pass

    text = get_text("vps_order_placed", user_lang, total=f"{total:.2f}")
    kb = get_vps_ordered_keyboard(user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer(get_text("vps_order_alert", user_lang), show_alert=True)
