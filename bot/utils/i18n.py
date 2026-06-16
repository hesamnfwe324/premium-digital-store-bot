import json
import os
from typing import Dict, Any, Optional
from bot.utils.logger import logger

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸", "native": "English"},
    "es": {"name": "Spanish", "flag": "🇪🇸", "native": "Español"},
    "fr": {"name": "French", "flag": "🇫🇷", "native": "Français"},
    "de": {"name": "German", "flag": "🇩🇪", "native": "Deutsch"},
    "ru": {"name": "Russian", "flag": "🇷🇺", "native": "Русский"},
    "zh": {"name": "Chinese", "flag": "🇨🇳", "native": "中文"},
    "ar": {"name": "Arabic", "flag": "🇸🇦", "native": "العربية"},
    "fa": {"name": "Persian", "flag": "🇮🇷", "native": "فارسی"},
}

DEFAULT_LANGUAGE = "en"


class I18n:
    def __init__(self):
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        locales_dir = os.path.join(os.path.dirname(__file__), "..", "..", "locales")
        for lang_code in SUPPORTED_LANGUAGES:
            file_path = os.path.join(locales_dir, f"{lang_code}.json")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._translations[lang_code] = json.load(f)
                logger.debug(f"Loaded locale: {lang_code}")
            except FileNotFoundError:
                logger.warning(f"Locale file not found: {lang_code}.json — using English fallback")
                self._translations[lang_code] = {}
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in locale {lang_code}: {e}")
                self._translations[lang_code] = {}

    def get(self, key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
        lang = lang if lang in self._translations else DEFAULT_LANGUAGE
        translations = self._translations.get(lang, {})
        text = translations.get(key)
        if text is None:
            text = self._translations.get(DEFAULT_LANGUAGE, {}).get(key, f"[{key}]")
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"i18n format error for key '{key}' lang '{lang}': {e}")
        return text

    def reload(self):
        self._translations.clear()
        self._load_translations()
        logger.info("Locales reloaded")


i18n = I18n()


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    return i18n.get(key, lang, **kwargs)
