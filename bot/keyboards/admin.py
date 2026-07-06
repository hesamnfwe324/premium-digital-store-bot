from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📊 Dashboard", callback_data="admin:dashboard"),
            InlineKeyboardButton(text="👥 Users", callback_data="admin:users"),
        ],
        [
            InlineKeyboardButton(text="📦 Products", callback_data="admin:products"),
            InlineKeyboardButton(text="🛒 Orders", callback_data="admin:orders"),
        ],
        [
            InlineKeyboardButton(text="💳 Payments", callback_data="admin:pending_payments"),
            InlineKeyboardButton(text="💰 Wallet Deposits", callback_data="admin:wallet_deposits"),
        ],
        [
            InlineKeyboardButton(text="🎁 Inventory", callback_data="admin_product:inventory"),
            InlineKeyboardButton(text="🎫 Discount Codes", callback_data="admin:discounts"),
        ],
        [
            InlineKeyboardButton(text="🎯 Referrals", callback_data="admin:referrals"),
            InlineKeyboardButton(text="🎫 Tickets", callback_data="admin:tickets"),
        ],
        [
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast"),
            InlineKeyboardButton(text="📈 Analytics", callback_data="admin:analytics"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Settings", callback_data="admin:settings"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_products_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="➕ Add Product", callback_data="admin_product:add"),
            InlineKeyboardButton(text="📋 List Products", callback_data="admin_product:list"),
        ],
        [
            InlineKeyboardButton(text="📦 Manage Inventory", callback_data="admin_product:inventory"),
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_orders_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="⏳ Pending", callback_data="admin_orders:pending"),
            InlineKeyboardButton(text="🔍 Validating", callback_data="admin_orders:validating"),
        ],
        [
            InlineKeyboardButton(text="✅ Delivered", callback_data="admin_orders:delivered"),
            InlineKeyboardButton(text="❌ Rejected", callback_data="admin_orders:rejected"),
        ],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_user_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_text = "✅ Unban User" if is_banned else "🚫 Ban User"
    ban_callback = f"admin_user:unban:{user_id}" if is_banned else f"admin_user:ban:{user_id}"
    buttons = [
        [InlineKeyboardButton(text=ban_text, callback_data=ban_callback)],
        [InlineKeyboardButton(text="💰 Add Balance", callback_data=f"admin_user:add_balance:{user_id}")],
        [InlineKeyboardButton(text="📋 View Orders", callback_data=f"admin_user:orders:{user_id}")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="admin:users")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
