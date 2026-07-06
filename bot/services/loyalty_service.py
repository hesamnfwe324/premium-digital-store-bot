from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class LoyaltyTier:
    key: str
    threshold: float
    bonus_percent: float
    emoji: str


# Ordered from highest to lowest so the first match wins.
LOYALTY_TIERS: List[LoyaltyTier] = [
    LoyaltyTier(key="platinum", threshold=500.0, bonus_percent=12.0, emoji="💎"),
    LoyaltyTier(key="gold", threshold=200.0, bonus_percent=9.0, emoji="🥇"),
    LoyaltyTier(key="silver", threshold=50.0, bonus_percent=7.0, emoji="🥈"),
    LoyaltyTier(key="bronze", threshold=0.0, bonus_percent=5.0, emoji="🥉"),
]


def get_tier_for_spend(total_spent: float) -> LoyaltyTier:
    for tier in LOYALTY_TIERS:
        if total_spent >= tier.threshold:
            return tier
    return LOYALTY_TIERS[-1]


def get_next_tier(total_spent: float) -> Optional[LoyaltyTier]:
    ordered = sorted(LOYALTY_TIERS, key=lambda t: t.threshold)
    for tier in ordered:
        if total_spent < tier.threshold:
            return tier
    return None


def get_referral_bonus_percent(total_spent: float) -> float:
    return get_tier_for_spend(total_spent).bonus_percent
