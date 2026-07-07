from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import CryptoCurrency, CRYPTO_NETWORK_NAMES, CRYPTO_EMOJIS
from bot.utils.i18n import get_text

# ─── Static data ──────────────────────────────────────────────────────────────

LOCATIONS = [
    {"id": "de",    "flag": "🇩🇪", "name_en": "Germany (Frankfurt)",     "name_fa": "آلمان (فرانکفورت)"},
    {"id": "nl",    "flag": "🇳🇱", "name_en": "Netherlands (Amsterdam)", "name_fa": "هلند (آمستردام)"},
    {"id": "fr",    "flag": "🇫🇷", "name_en": "France (Paris)",          "name_fa": "فرانسه (پاریس)"},
    {"id": "us_ny", "flag": "🇺🇸", "name_en": "USA (New York)",          "name_fa": "آمریکا (نیویورک)"},
    {"id": "us_la", "flag": "🇺🇸", "name_en": "USA (Los Angeles)",       "name_fa": "آمریکا (لس‌آنجلس)"},
    {"id": "sg",    "flag": "🇸🇬", "name_en": "Singapore",               "name_fa": "سنگاپور"},
    {"id": "tr",    "flag": "🇹🇷", "name_en": "Turkey (Istanbul)",       "name_fa": "ترکیه (استانبول)"},
    {"id": "fi",    "flag": "🇫🇮", "name_en": "Finland (Helsinki)",      "name_fa": "فنلاند (هلسینکی)"},
]

VPS_PLANS = [
    {
        "id": "starter",
        "name": "⚡ Starter",
        "cpu": "1 vCPU",
        "ram": "1 GB DDR4",
        "disk": "20 GB SSD",
        "bandwidth": "1 TB",
        "network": "100 Mbps",
        "use_case_en": "Telegram bots, small websites, testing",
        "use_case_fa": "ربات تلگرام، سایت کوچک، تست",
        "price": 10.0,
    },
    {
        "id": "basic",
        "name": "🔹 Basic",
        "cpu": "2 vCPU",
        "ram": "2 GB DDR4",
        "disk": "40 GB SSD",
        "bandwidth": "2 TB",
        "network": "200 Mbps",
        "use_case_en": "Dev environments, small web apps, lightweight APIs",
        "use_case_fa": "محیط توسعه، اپ کوچک، API سبک",
        "price": 18.0,
    },
    {
        "id": "standard",
        "name": "🔷 Standard",
        "cpu": "2 vCPU",
        "ram": "4 GB DDR4",
        "disk": "60 GB SSD",
        "bandwidth": "4 TB",
        "network": "400 Mbps",
        "use_case_en": "Medium websites, REST APIs, game servers, VPN",
        "use_case_fa": "سایت متوسط، API، سرور بازی، VPN",
        "price": 28.0,
    },
    {
        "id": "pro",
        "name": "🟣 Pro",
        "cpu": "4 vCPU",
        "ram": "8 GB DDR4",
        "disk": "80 GB NVMe",
        "bandwidth": "8 TB",
        "network": "1 Gbps",
        "use_case_en": "High-traffic apps, databases, media streaming",
        "use_case_fa": "اپ پرترافیک، دیتابیس، استریم مدیا",
        "price": 42.0,
    },
    {
        "id": "business",
        "name": "💼 Business",
        "cpu": "8 vCPU",
        "ram": "16 GB DDR4",
        "disk": "160 GB NVMe",
        "bandwidth": "Unlimited",
        "network": "1 Gbps",
        "use_case_en": "Enterprise apps, e-commerce, multi-service hosting",
        "use_case_fa": "اپ سازمانی، فروشگاه اینترنتی، هاستینگ",
        "price": 58.0,
    },
    {
        "id": "enterprise",
        "name": "🏆 Enterprise",
        "cpu": "16 vCPU",
        "ram": "32 GB DDR4",
        "disk": "320 GB NVMe",
        "bandwidth": "Unlimited",
        "network": "10 Gbps",
        "use_case_en": "Large-scale platforms, SaaS products, hosting providers",
        "use_case_fa": "پلتفرم بزرگ، محصولات SaaS، هاستینگ",
        "price": 75.0,
    },
]

DEDICATED_PLANS = [
    {
        "id": "ded_basic",
        "name": "🖥 Dedicated Basic",
        "cpu": "Intel Xeon E3-1230 v6 (4C/8T @ 3.5GHz)",
        "ram": "16 GB DDR4 ECC",
        "disk": "2× 1 TB HDD (RAID 1)",
        "bandwidth": "Unlimited",
        "network": "1 Gbps",
        "gpu_support": False,
        "use_case_en": "Dedicated resources, root access, SMB hosting",
        "use_case_fa": "منابع اختصاصی، دسترسی کامل، هاستینگ SMB",
        "price": 100.0,
    },
    {
        "id": "ded_standard",
        "name": "🖥 Dedicated Standard",
        "cpu": "Intel Xeon E5-2680 v4 (14C/28T @ 2.4GHz)",
        "ram": "32 GB DDR4 ECC",
        "disk": "2 TB HDD + 480 GB SSD",
        "bandwidth": "Unlimited",
        "network": "1 Gbps",
        "gpu_support": False,
        "use_case_en": "High-load databases, media servers, trading bots",
        "use_case_fa": "دیتابیس پرباری، سرور مدیا، ربات معامله",
        "price": 185.0,
    },
    {
        "id": "ded_pro",
        "name": "🖥 Dedicated Pro",
        "cpu": "2× Xeon E5-2697 v4 (18C/36T each)",
        "ram": "64 GB DDR4 ECC",
        "disk": "4 TB HDD + 960 GB NVMe",
        "bandwidth": "Unlimited",
        "network": "10 Gbps",
        "gpu_support": True,
        "use_case_en": "AI workloads, video rendering, large databases",
        "use_case_fa": "هوش مصنوعی، رندرینگ ویدیو، دیتابیس بزرگ",
        "price": 320.0,
    },
    {
        "id": "ded_gpu",
        "name": "🎮 GPU Server",
        "cpu": "Intel Xeon Gold 6226R (16C/32T @ 2.9GHz)",
        "ram": "128 GB DDR4 ECC",
        "disk": "8 TB NVMe (RAID 10)",
        "bandwidth": "Unlimited",
        "network": "10 Gbps",
        "gpu_support": True,
        "use_case_en": "Deep learning, 3D rendering, LLM inference",
        "use_case_fa": "یادگیری عمیق، رندر سه‌بعدی، استنتاج LLM",
        "price": 480.0,
    },
]

GPU_OPTIONS = [
    {"id": "no_gpu",  "name_en": "No GPU (free)",              "name_fa": "بدون GPU (رایگان)",           "extra": 0},
    {"id": "rtx3060", "name_en": "NVIDIA RTX 3060 12GB GDDR6", "name_fa": "NVIDIA RTX 3060 12 گیگ GDDR6","extra": 60},
    {"id": "rtx3080", "name_en": "NVIDIA RTX 3080 10GB GDDR6X","name_fa": "NVIDIA RTX 3080 10 گیگ GDDR6X","extra": 100},
    {"id": "a100",    "name_en": "NVIDIA A100 80GB HBM2e",     "name_fa": "NVIDIA A100 80 گیگ HBM2e",    "extra": 320},
]

DURATION_OPTIONS = [
    {"id": "1m",  "name_en": "1 Month",         "name_fa": "۱ ماه",             "months": 1,  "discount": 0},
    {"id": "3m",  "name_en": "3 Months (-10%)", "name_fa": "۳ ماه (-۱۰٪)",     "months": 3,  "discount": 10},
    {"id": "6m",  "name_en": "6 Months (-15%)", "name_fa": "۶ ماه (-۱۵٪)",     "months": 6,  "discount": 15},
    {"id": "12m", "name_en": "12 Months (-20%)","name_fa": "۱۲ ماه (-۲۰٪)",    "months": 12, "discount": 20},
]

OS_OPTIONS = [
    {"id": "ubuntu2004", "name": "Ubuntu 20.04 LTS"},
    {"id": "ubuntu2204", "name": "Ubuntu 22.04 LTS"},
    {"id": "ubuntu2404", "name": "Ubuntu 24.04 LTS"},
    {"id": "debian11",   "name": "Debian 11 Bullseye"},
    {"id": "debian12",   "name": "Debian 12 Bookworm"},
    {"id": "centos7",    "name": "CentOS 7"},
    {"id": "win2019",    "name": "Windows Server 2019"},
    {"id": "win2022",    "name": "Windows Server 2022"},
]

# ─── Compact button labels (no extra spaces — fit Telegram button width) ───────
# Format: "EMOJI Name | Specs | Price"
_PLAN_LABELS = {
    "starter":      "⚡ Starter | 1vCPU 1GB 20GB | $10/mo",
    "basic":        "🔹 Basic | 2vCPU 2GB 40GB | $18/mo",
    "standard":     "🔷 Standard | 2vCPU 4GB 60GB | $28/mo",
    "pro":          "🟣 Pro | 4vCPU 8GB NVMe | $42/mo",
    "business":     "💼 Business | 8vCPU 16GB NVMe | $58/mo",
    "enterprise":   "🏆 Enterprise | 16vCPU 32GB NVMe | $75/mo",
    "ded_basic":    "🖥 Ded Basic | Xeon E3 16GB 2×1TB | $100/mo",
    "ded_standard": "🖥 Ded Standard | Xeon E5 32GB | $185/mo",
    "ded_pro":      "🖥 Ded Pro | 2×Xeon E5 64GB | $320/mo",
    "ded_gpu":      "🎮 GPU Server | Xeon Gold 128GB | $480/mo",
}

# ─── Helper lookups ────────────────────────────────────────────────────────────

def get_location_by_id(loc_id: str) -> dict:
    return next((l for l in LOCATIONS if l["id"] == loc_id), {})

def get_plan_by_id(plan_id: str) -> dict:
    return next((p for p in VPS_PLANS + DEDICATED_PLANS if p["id"] == plan_id), {})

def get_gpu_by_id(gpu_id: str) -> dict:
    return next((g for g in GPU_OPTIONS if g["id"] == gpu_id), {})

def get_duration_by_id(dur_id: str) -> dict:
    return next((d for d in DURATION_OPTIONS if d["id"] == dur_id), {})

def get_os_by_id(os_id: str) -> dict:
    return next((o for o in OS_OPTIONS if o["id"] == os_id), {})

def calculate_total(plan: dict, gpu: dict, duration: dict) -> float:
    base = (plan.get("price", 0) + gpu.get("extra", 0)) * duration.get("months", 1)
    discount = duration.get("discount", 0) / 100
    return round(base * (1 - discount), 2)

# ─── Keyboard builders ────────────────────────────────────────────────────────
# Back-button routing (all verified correct):
#
#  Type KB        → Back: menu:home
#  Location KB    → Back: vps:start              → handle_vps_start → Type KB
#  Plan KB        → Back: vps:back:loc:{t}       → handle_vps_back_to_location → Location KB
#  GPU KB         → Back: vps:loc:{t}:{loc}      → handle_vps_location → Plan KB
#  Duration KB    → Back (GPU path):   vps:plan:{t}:{loc}:{plan}   → handle_vps_plan → GPU KB
#  Duration KB    → Back (noGPU path): vps:loc:{t}:{loc}           → handle_vps_location → Plan KB
#  OS KB          → Back: vps:showdur:{t}:{loc}:{plan}:{gpu}       → show Duration KB
#  Confirm KB     → Back: vps:showos:{t}:{loc}:{plan}:{gpu}:{dur}  → show OS KB


def get_vps_type_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_vps_virtual"),   callback_data="vps:type:virtual")],
        [InlineKeyboardButton(text=t("btn_vps_dedicated"), callback_data="vps:type:dedicated")],
        [InlineKeyboardButton(text=t("btn_home"),          callback_data="menu:home")],
    ])


def get_vps_location_keyboard(server_type: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = []
    row = []
    for loc in LOCATIONS:
        short = (loc["name_fa"] if lang == "fa" else loc["name_en"]).split("(")[0].strip()
        row.append(InlineKeyboardButton(
            text=f"{loc['flag']} {short}",
            callback_data=f"vps:loc:{server_type}:{loc['id']}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    # Back → Type keyboard
    buttons.append([InlineKeyboardButton(text=t("btn_back"), callback_data="vps:start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_plan_keyboard(server_type: str, location_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    plans = VPS_PLANS if server_type == "virtual" else DEDICATED_PLANS
    buttons = [
        [InlineKeyboardButton(
            text=_PLAN_LABELS.get(p["id"], p["name"]),
            callback_data=f"vps:plan:{server_type}:{location_id}:{p['id']}"
        )]
        for p in plans
    ]
    # Back → Location keyboard
    buttons.append([InlineKeyboardButton(
        text=t("btn_back"),
        callback_data=f"vps:back:loc:{server_type}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_gpu_keyboard(server_type: str, location_id: str, plan_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = []
    for gpu in GPU_OPTIONS:
        name = gpu["name_fa"] if lang == "fa" else gpu["name_en"]
        extra = f"  +${gpu['extra']}/mo" if gpu["extra"] > 0 else ""
        buttons.append([InlineKeyboardButton(
            text=f"{'🎮' if gpu['id'] != 'no_gpu' else '❌'} {name}{extra}",
            callback_data=f"vps:gpu:{server_type}:{location_id}:{plan_id}:{gpu['id']}"
        )])
    # Back → Plan list (re-show plan keyboard via location handler)
    buttons.append([InlineKeyboardButton(
        text=t("btn_back"),
        callback_data=f"vps:loc:{server_type}:{location_id}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_duration_keyboard(server_type: str, location_id: str, plan_id: str,
                               gpu_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    plan = get_plan_by_id(plan_id)
    gpu  = get_gpu_by_id(gpu_id)
    buttons = []
    for dur in DURATION_OPTIONS:
        name  = dur["name_fa"] if lang == "fa" else dur["name_en"]
        total = calculate_total(plan, gpu, dur)
        buttons.append([InlineKeyboardButton(
            text=f"{name}  —  ${total:.2f} total",
            callback_data=f"vps:dur:{server_type}:{location_id}:{plan_id}:{gpu_id}:{dur['id']}"
        )])
    # Back routing:
    #   GPU-capable plan → back to GPU selection (re-trigger plan handler which shows GPU KB)
    #   Non-GPU plan     → back to plan list (re-trigger location handler)
    if plan.get("gpu_support"):
        back_cb = f"vps:plan:{server_type}:{location_id}:{plan_id}"
    else:
        back_cb = f"vps:loc:{server_type}:{location_id}"
    buttons.append([InlineKeyboardButton(text=t("btn_back"), callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_os_keyboard(server_type: str, location_id: str, plan_id: str,
                         gpu_id: str, dur_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(
            text=f"🐧 {os['name']}" if "Ubuntu" in os["name"] or "Debian" in os["name"] or "CentOS" in os["name"]
                 else f"🪟 {os['name']}" if "Windows" in os["name"]
                 else os["name"],
            callback_data=f"vps:os:{server_type}:{location_id}:{plan_id}:{gpu_id}:{dur_id}:{os['id']}"
        )]
        for os in OS_OPTIONS
    ]
    # Back → Duration keyboard (dedicated back handler)
    buttons.append([InlineKeyboardButton(
        text=t("btn_back"),
        callback_data=f"vps:showdur:{server_type}:{location_id}:{plan_id}:{gpu_id}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_confirm_keyboard(server_type: str, location_id: str, plan_id: str,
                              gpu_id: str, dur_id: str, os_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn_vps_order_now"),
            callback_data=f"vps:confirm:{server_type}:{location_id}:{plan_id}:{gpu_id}:{dur_id}:{os_id}"
        )],
        # Back → OS keyboard (dedicated back handler)
        [InlineKeyboardButton(
            text=t("btn_back"),
            callback_data=f"vps:showos:{server_type}:{location_id}:{plan_id}:{gpu_id}:{dur_id}"
        )],
    ])


def get_vps_crypto_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Mirrors the regular payment crypto keyboard — identical UX for users."""
    t = lambda key: get_text(key, lang)
    buttons = []
    row = []
    for currency, name in CRYPTO_NETWORK_NAMES.items():
        emoji = CRYPTO_EMOJIS.get(currency, "💰")
        short = currency.value.replace("_", " ")
        row.append(InlineKeyboardButton(
            text=f"{emoji} {short}",
            callback_data=f"vps_pay:{currency.value}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=t("btn_home"), callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vps_payment_admin_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm VPS Payment", callback_data=f"vps_confirm_pay:{payment_id}"),
            InlineKeyboardButton(text="❌ Reject",              callback_data=f"vps_reject_pay:{payment_id}"),
        ]
    ])


def get_vps_ordered_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 " + t("btn_support"), callback_data="menu:support")],
        [InlineKeyboardButton(text=t("btn_home"),            callback_data="menu:home")],
    ])
