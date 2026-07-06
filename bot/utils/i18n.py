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
        # Build a lookup set of all known "instant delivery" values across all languages
        self._instant_delivery_values: set = set()
        self._build_instant_delivery_lookup()

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

    def _build_instant_delivery_lookup(self):
        """Collect all known delivery_instant values across all languages (case-insensitive).
        Also adds common Persian/Arabic script variants so that values entered by admins
        in either script (e.g. 'فوری' vs 'فوري') are recognized correctly.
        """
        # Explicit Persian/Arabic aliases for instant delivery that admins commonly type
        _extra_aliases = {"فوری", "فوري", "آنی", "آني", "فورى", "instant", "sofort",
                          "мгновенно", "即时", "inmediata", "immédiate"}
        for lang_code, translations in self._translations.items():
            value = translations.get("delivery_instant", "")
            if value:
                self._instant_delivery_values.add(value.strip().lower())
        for alias in _extra_aliases:
            self._instant_delivery_values.add(alias.lower())

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

    def normalize_delivery_time(self, delivery_time: str, lang: str = DEFAULT_LANGUAGE) -> str:
        """
        Translate a stored delivery_time value to the user's language.

        If the stored value matches any known 'delivery_instant' translation
        (e.g. 'فوری', 'Instant', 'فوري', 'Sofort', etc.), return the correct
        translation for the requested language.  Otherwise return the value as-is.
        """
        if not delivery_time:
            return delivery_time
        if delivery_time.strip().lower() in self._instant_delivery_values:
            return self.get("delivery_instant", lang)
        return delivery_time

    def reload(self):
        self._translations.clear()
        self._load_translations()
        self._instant_delivery_values.clear()
        self._build_instant_delivery_lookup()
        logger.info("Locales reloaded")


i18n = I18n()


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    return i18n.get(key, lang, **kwargs)


def normalize_delivery_time(delivery_time: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Translate a stored delivery_time value to the user's current language."""
    return i18n.normalize_delivery_time(delivery_time, lang)
