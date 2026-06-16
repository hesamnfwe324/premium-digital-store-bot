import random
import string
from datetime import datetime, timezone


def generate_order_number() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD-{timestamp}-{suffix}"


def generate_payment_reference() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PAY-{timestamp}-{suffix}"


def generate_ticket_number() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=5))
    return f"TKT-{timestamp}-{suffix}"


def generate_referral_code(telegram_id: int) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"REF{telegram_id % 10000:04d}{suffix}"


def format_price(amount: float) -> str:
    return f"{amount:.2f}"


def format_datetime(dt: datetime) -> str:
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def mask_card_number(card_number: str) -> str:
    if not card_number or len(card_number) < 4:
        return "****"
    return "*" * (len(card_number) - 4) + card_number[-4:]
