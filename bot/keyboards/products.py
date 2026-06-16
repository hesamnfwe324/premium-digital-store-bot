from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Product
from bot.utils.i18n import get_text


def get_products_keyboard(products: List[Product], lang: str = "en", back_callback: str = "menu:home") -> InlineKeyboardMarkup:
    buttons = []
    for product in products:
        stock_emoji = "✅" if product.quantity > 0 else "❌"
        name = product.get_name(lang)
        buttons.append([
            InlineKeyboardButton(
                text=f"{stock_emoji} {name} — ${product.price_usdt:.2f}",
                callback_data=f"product:{product.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=back_callback)
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_detail_keyboard(product_id: int, lang: str = "en", back_callback: str = "menu:home") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [InlineKeyboardButton(text=t("btn_buy_now"), callback_data=f"buy:{product_id}")],
        [InlineKeyboardButton(text=t("btn_back"), callback_data=back_callback)],
        [InlineKeyboardButton(text=t("btn_home"), callback_data="menu:home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_gift_card_categories_keyboard(categories: List[str], lang: str = "en") -> InlineKeyboardMarkup:
    GIFT_CARD_EMOJIS = {
        "amazon": "📦", "apple": "🍎", "google play": "▶️", "steam": "🎮",
        "playstation": "🎮", "xbox": "🎮", "netflix": "🎬", "spotify": "🎵",
        "binance": "🟡", "razer": "🎯"
    }
    buttons = []
    for i in range(0, len(categories), 2):
        row = []
        for brand in categories[i:i+2]:
            emoji = GIFT_CARD_EMOJIS.get(brand.lower(), "🎁")
            row.append(InlineKeyboardButton(
                text=f"{emoji} {brand}",
                callback_data=f"gift_brand:{brand.lower()}"
            ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
