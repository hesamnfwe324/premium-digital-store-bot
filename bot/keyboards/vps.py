from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.i18n import get_text

# ─── VPS Plan data (stored here, no DB needed) ───────────────────────────────

VPS_LOCATIONS = [
    {"id": "de", "flag": "🇩🇪", "name_en": "Germany (Frankfurt)", "name_fa": "آلمان (فرانکفورت)"},
    {"id": "nl", "flag": "🇳🇱", "name_en": "Netherlands (Amsterdam)", "name_fa": "هلند (آمستردام)"},
    {"id": "fr", "flag": "🇫🇷", "name_en": "France (Paris)", "name_fa": "فرانسه (پاریس)"},
    {"id": "us_ny", "flag": "🇺🇸", "name_en": "USA (New York)", "name_fa": "آمریکا (نیویورک)"},
    {"id": "us_la", "flag": "🇺🇸", "name_en": "USA (Los Angeles)", "name_fa": "آمریکا (لس‌آنجلس)"},
    {"id": "sg", "flag": "🇸🇬", "name_en": "Singapore", "name_fa": "سنگاپور"},
    {"id": "tr", "flag": "🇹🇷", "name_en": "Turkey (Istanbul)", "name_fa": "ترکیه (استانبول)"},
    {"id": "fi", "flag": "🇫🇮", "name_en": "Finland (Helsinki)", "name_fa": "فنلاند (هلسینکی)"},
]

VPS_PLANS = [
    {
        "id": "starter",
        "name": "⚡ Starter",
        "cpu": "1 vCPU",
        "ram": "1 GB",
        "disk": "20 GB SSD",
        "bandwidth": "1 TB",
        "price": 3.0,
    },
    {
        "id": "basic",
        "name": "🔹 Basic",
        "cpu": "2 vCPU",
        "ram": "2 GB",
        "disk": "40 GB SSD",
        "bandwidth": "2 TB",
        "price": 6.0,
    },
    {
        "id": "standard",
        "name": "🔷 Standard",
        "cpu": "2 vCPU",
        "ram": "4 GB",
        "disk": "60 GB SSD",
        "bandwidth": "4 TB",
        "price": 10.0,
    },
    {
        "id": "pro",
        "name": "🟣 Pro",
        "cpu": "4 vCPU",
        "ram": "8 GB",
        "disk": "80 GB NVMe",
        "bandwidth": "8 TB",
        "price": 18.0,
    },
    {
        "id": "business",
        "name": "💼 Business",
        "cpu": "8 vCPU",
        "ram": "16 GB",
        "disk": "160 GB NVMe",
        "bandwidth": "Unlimited",
        "price": 32.0,
    },
    {
        "id": "enterprise",
        "name": "🏆 Enterprise",
        "cpu": "16 vCPU",
        "ram": "32 GB",
        "disk": "320 GB NVMe",
        "bandwidth": "Unlimited",
        "price": 60.0,
    },
]

DEDICATED_PLANS = [
    {
        "id": "ded_basic",
        "name": "🖥 Dedicated Basic",
        "cpu": "Intel Xeon E3 (4 cores / 8 threads)",
        "ram": "16 GB DDR4",
        "disk": "1 TB HDD",
        "bandwidth": "Unlimited",
        "gpu_support": False,
        "price": 80.0,
    },
    {
        "id": "ded_standard",
        "name": "🖥 Dedicated Standard",
        "cpu": "Intel Xeon E5 (8 cores / 16 threads)",
        "ram": "32 GB DDR4",
        "disk": "2 TB HDD + 240 GB SSD",
        "bandwidth": "Unlimited",
        "gpu_support": False,
        "price": 150.0,
    },
    {
        "id": "ded_pro",
        "name": "🖥 Dedicated Pro",
        "cpu": "Intel Xeon E5 v4 (12 cores / 24 threads)",
        "ram": "64 GB DDR4",
        "disk": "4 TB HDD + 480 GB NVMe",
        "bandwidth": "Unlimited",
        "gpu_support": True,
        "price": 280.0,
    },
    {
        "id": "ded_gpu",
        "name": "🎮 GPU Server",
        "cpu": "Intel Xeon Gold (16 cores / 32 threads)",
        "ram": "128 GB DDR4 ECC",
        "disk": "8 TB NVMe RAID",
        "bandwidth": "Unlimited",
        "gpu_support": True,
        "price": 480.0,
    },
]

GPU_OPTIONS = [
    {"id": "no_gpu", "name_en": "❌ No GPU", "name_fa": "❌ بدون GPU", "extra": 0},
    {"id": "rtx3060", "name_en": "🎮 NVIDIA RTX 3060 (12 GB)", "name_fa": "🎮 NVIDIA RTX 3060 (12 گیگ)", "extra": 60},
    {"id": "rtx3080", "name_en": "🎮 NVIDIA RTX 3080 (10 GB)", "name_fa": "🎮 NVIDIA RTX 3080 (10 گیگ)", "extra": 110},
    {"id": "a100", "name_en": "🚀 NVIDIA A100 (80 GB)", "name_fa": "🚀 NVIDIA A100 (80 گیگ)", "extra": 350},
]

DURATION_OPTIONS = [
    {"id": "1m", "name_en": "1 Month", "name_fa": "۱ ماه", "months": 1, "discount": 0},
    {"id": "3m", "name_en": "3 Months (-10%)", "name_fa": "۳ ماه (۱۰٪ تخفیف)", "months": 3, "discount": 10},
    {"id": "6m", "name_en": "6 Months (-15%)", "name_fa": "۶ ماه (۱۵٪ تخفیف)", "months": 6, "discount": 15},
    {"id": "12m", "name_en": "12 Months (-20%)", "name_fa": "۱۲ ماه (۲۰٪ تخفیف)", "months": 12, "discount": 20},
]

OS_OPTIONS = [
    {"id": "ubuntu2004", "name": "🐧 Ubuntu 20.04 LTS"},
    {"id": "ubuntu2204", "name": "🐧 Ubuntu 22.04 LTS"},
    {"id": "debian11", "name": "🌀 Debian 11"},
    {"id": "debian12", "name": "🌀 Debian 12"},
    {"id": "centos7", "name": "🎩 CentOS 7"},
    {"id": "win2019", "name": "🪟 Windows Server 2019"},
    {"id": "win2022", "name": "🪟 Windows Server 2022"},
]

# ─── Keyboard builders ────────────────────────────────────────────────────────

def get_vps_type_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_vps_virtual"), callback_data="vps:type:virtual"),
            InlineKeyboardButton(text=t("btn_vps_dedicated"), callback_data="vps:type:dedicated"),
        ],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_location_keyboard(server_type: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = []
    for i in range(0, len(VPS_LOCATIONS), 2):
        row = []
        for loc in VPS_LOCATIONS[i:i+2]:
            lname = loc["name_fa"] if lang == "fa" else loc["name_en"]
            row.append(InlineKeyboardButton(
                text=f"{loc['flag']} {lname}",
                callback_data=f"vps:loc:{server_type}:{loc['id']}",
            ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=t("btn_back"), callback_data="vps:start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_plan_keyboard(server_type: str, location_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    plans = DEDICATED_PLANS if server_type == "dedicated" else VPS_PLANS
    buttons = []
    for plan in plans:
        label = f"{plan['name']} — ${plan['price']:.0f}/mo"
        buttons.append([InlineKeyboardButton(
            text=label,
            callback_data=f"vps:plan:{server_type}:{location_id}:{plan['id']}",
        )])
    buttons.append([InlineKeyboardButton(text=t("btn_back"), callback_data=f"vps:location:{server_type}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_gpu_keyboard(server_type: str, location_id: str, plan_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = []
    for gpu in GPU_OPTIONS:
        gname = gpu["name_fa"] if lang == "fa" else gpu["name_en"]
        extra_text = f" (+${gpu['extra']}/mo)" if gpu["extra"] > 0 else ""
        buttons.append([InlineKeyboardButton(
            text=f"{gname}{extra_text}",
            callback_data=f"vps:gpu:{server_type}:{location_id}:{plan_id}:{gpu['id']}",
        )])
    buttons.append([InlineKeyboardButton(text=t("btn_back"), callback_data=f"vps:location:{server_type}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_duration_keyboard(server_type: str, location_id: str, plan_id: str, gpu_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = []
    for d in DURATION_OPTIONS:
        dname = d["name_fa"] if lang == "fa" else d["name_en"]
        buttons.append([InlineKeyboardButton(
            text=dname,
            callback_data=f"vps:dur:{server_type}:{location_id}:{plan_id}:{gpu_id}:{d['id']}",
        )])
    buttons.append([InlineKeyboardButton(text=t("btn_back"), callback_data=f"vps:location:{server_type}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_os_keyboard(server_type: str, location_id: str, plan_id: str, gpu_id: str, duration_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = []
    for os_opt in OS_OPTIONS:
        buttons.append([InlineKeyboardButton(
            text=os_opt["name"],
            callback_data=f"vps:os:{server_type}:{location_id}:{plan_id}:{gpu_id}:{duration_id}:{os_opt['id']}",
        )])
    buttons.append([InlineKeyboardButton(text=t("btn_back"), callback_data=f"vps:location:{server_type}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_confirm_keyboard(server_type: str, location_id: str, plan_id: str,
                              gpu_id: str, duration_id: str, os_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    order_data = f"{server_type}:{location_id}:{plan_id}:{gpu_id}:{duration_id}:{os_id}"
    buttons = [
        [InlineKeyboardButton(text=t("btn_vps_order_now"), callback_data=f"vps:confirm:{order_data}")],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="vps:start")],
        [InlineKeyboardButton(text=t("btn_home"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_ordered_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(text=t("btn_contact_support"), url="https://t.me/VPS24H")],
        [InlineKeyboardButton(text=t("btn_home"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Helper lookups ───────────────────────────────────────────────────────────

def get_location_by_id(loc_id: str) -> dict:
    return next((l for l in VPS_LOCATIONS if l["id"] == loc_id), {})

def get_plan_by_id(plan_id: str, server_type: str) -> dict:
    plans = DEDICATED_PLANS if server_type == "dedicated" else VPS_PLANS
    return next((p for p in plans if p["id"] == plan_id), {})

def get_gpu_by_id(gpu_id: str) -> dict:
    return next((g for g in GPU_OPTIONS if g["id"] == gpu_id), {})

def get_duration_by_id(dur_id: str) -> dict:
    return next((d for d in DURATION_OPTIONS if d["id"] == dur_id), {})

def get_os_by_id(os_id: str) -> dict:
    return next((o for o in OS_OPTIONS if o["id"] == os_id), {})

def calculate_total(plan: dict, gpu: dict, duration: dict) -> float:
    base = (plan.get("price", 0) + gpu.get("extra", 0)) * duration.get("months", 1)
    discount = duration.get("discount", 0)
    return round(base * (1 - discount / 100), 2)
