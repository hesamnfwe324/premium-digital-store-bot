from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.i18n import get_text

SUPPORT_URL = "https://t.me/VPS24H"


def get_account_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(text=t("btn_my_orders"), callback_data="menu:my_orders")],
        [InlineKeyboardButton(text=t("btn_wallet"), callback_data="menu:wallet")],
        [InlineKeyboardButton(text=t("btn_referral"), callback_data="menu:referral")],
        [InlineKeyboardButton(text=t("btn_loyalty"), callback_data="menu:loyalty")],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_wallet_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Wallet screen: Top Up | History | Back."""
    t = lambda key: get_text(key, lang)
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_topup_wallet"), callback_data="wallet:topup"),
            InlineKeyboardButton(text=t("btn_tx_history"), callback_data="wallet:history"),
        ],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="menu:my_account")],
        [InlineKeyboardButton(text=t("btn_home"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_orders_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(text=t("btn_active_orders"), callback_data="orders:active")],
        [InlineKeyboardButton(text=t("btn_completed_orders"), callback_data="orders:completed")],
        [InlineKeyboardButton(text=t("btn_cancelled_orders"), callback_data="orders:cancelled")],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(text=t("btn_change_language"), callback_data="settings:language")],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_support_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(text=t("btn_contact_support"), url=SUPPORT_URL)],
        [InlineKeyboardButton(text=t("btn_open_ticket"), callback_data="support:open_ticket")],
        [InlineKeyboardButton(text=t("btn_view_tickets"), callback_data="support:my_tickets")],
        [InlineKeyboardButton(text=t("btn_faq"), callback_data="support:faq")],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard(lang: str = "en", callback: str = "menu:home") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=callback)],
        [InlineKeyboardButton(text=get_text("btn_home", lang), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
