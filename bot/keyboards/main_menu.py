from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.i18n import get_text


def get_main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    t = lambda key: get_text(key, lang)
    buttons = [
        [
            InlineKeyboardButton(text=t("btn_visa_cards"), callback_data="menu:visa_cards"),
            InlineKeyboardButton(text=t("btn_mastercards"), callback_data="menu:mastercards"),
        ],
        [
            InlineKeyboardButton(text=t("btn_gift_cards"), callback_data="menu:gift_cards"),
            InlineKeyboardButton(text=t("btn_premium_services"), callback_data="menu:premium_services"),
        ],
        [
            InlineKeyboardButton(text=t("btn_my_orders"), callback_data="menu:my_orders"),
            InlineKeyboardButton(text=t("btn_my_account"), callback_data="menu:my_account"),
        ],
        [
            InlineKeyboardButton(text=t("btn_wallet"), callback_data="menu:wallet"),
            InlineKeyboardButton(text=t("btn_referral"), callback_data="menu:referral"),
        ],
        [
            InlineKeyboardButton(text=t("btn_flash_deals"), callback_data="menu:deals"),
            InlineKeyboardButton(text=t("btn_best_sellers"), callback_data="menu:best_sellers"),
        ],
        [
            InlineKeyboardButton(text=t("btn_loyalty"), callback_data="menu:loyalty"),
            InlineKeyboardButton(text=t("btn_gift_reward"), callback_data="menu:gift_reward"),
        ],
        [
            InlineKeyboardButton(text=t("btn_discount_codes"), callback_data="menu:discount_codes"),
            InlineKeyboardButton(text=t("btn_tutorials"), callback_data="menu:tutorials"),
        ],
        [
            InlineKeyboardButton(text=t("btn_support"), callback_data="menu:support"),
            InlineKeyboardButton(text=t("btn_settings"), callback_data="menu:settings"),
        ],
        [
            InlineKeyboardButton(text=t("btn_join_channel"), callback_data="menu:join_channel"),
            InlineKeyboardButton(text=t("btn_terms"), callback_data="menu:terms"),
        ],
        [
            InlineKeyboardButton(text=t("btn_vps_virtual"), callback_data="vps:type:virtual"),
            InlineKeyboardButton(text=t("btn_vps_dedicated"), callback_data="vps:type:dedicated"),
        ],
        [
            InlineKeyboardButton(text=t("btn_about"), callback_data="menu:about"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
