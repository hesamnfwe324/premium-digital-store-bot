from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import CryptoCurrency, CRYPTO_NETWORK_NAMES, CRYPTO_EMOJIS
from bot.utils.i18n import get_text


def get_wallet_pay_keyboard(product_id: int, lang: str = "en", balance: float = 0.0) -> InlineKeyboardMarkup:
    """Payment method selection when wallet has sufficient balance."""
    t = lambda key: get_text(key, lang)
    btn_wallet_label = t("btn_pay_from_wallet") + f" (${balance:.2f})"
    buttons = [
        [InlineKeyboardButton(text=btn_wallet_label, callback_data=f"wallet_pay:{product_id}")],
        [InlineKeyboardButton(text="💳 " + t("btn_pay_now"), callback_data=f"buy_crypto:{product_id}")],
        [InlineKeyboardButton(text=t("btn_back"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_crypto_keyboard(order_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, (currency, name) in enumerate(CRYPTO_NETWORK_NAMES.items()):
        emoji = CRYPTO_EMOJIS.get(currency, "💰")
        short_name = currency.value.replace("_", " ")
        row.append(InlineKeyboardButton(
            text=f"{emoji} {short_name}",
            callback_data=f"crypto:{order_id}:{currency.value}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=f"product_back:{order_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_submitted_keyboard(payment_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(text=t("btn_submit_txid"), callback_data=f"submit_txid:{payment_id}")],
        [InlineKeyboardButton(text=t("btn_home"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_confirm_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirm Payment", callback_data=f"admin_confirm_pay:{payment_id}"),
            InlineKeyboardButton(text="❌ Reject Payment", callback_data=f"admin_reject_pay:{payment_id}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
