from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.i18n import SUPPORTED_LANGUAGES


def get_language_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    lang_items = list(SUPPORTED_LANGUAGES.items())
    for i in range(0, len(lang_items), 2):
        row = []
        for code, info in lang_items[i:i+2]:
            row.append(
                InlineKeyboardButton(
                    text=f"{info['flag']} {info['native']}",
                    callback_data=f"lang:{code}"
                )
            )
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
