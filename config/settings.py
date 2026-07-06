import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str
    ADMIN_IDS: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/premiumstore"

    WEBHOOK_ENABLED: bool = False
    WEBHOOK_HOST: str = "https://example.onrender.com"
    WEBHOOK_PATH: str = "/webhook"
    # Render injects PORT automatically — fall back to 8000 for local dev
    WEBHOOK_PORT: int = int(os.environ.get("PORT", 8000))

    USDT_TRC20_ADDRESS: str = "TReplaceWithYourTRC20Address"
    USDT_BEP20_ADDRESS: str = "0xReplaceWithYourBEP20Address"
    BTC_ADDRESS: str = "bc1ReplaceWithYourBTCAddress"
    ETH_ADDRESS: str = "0xReplaceWithYourETHAddress"
    BNB_ADDRESS: str = "0xReplaceWithYourBNBAddress"
    TON_ADDRESS: str = "UQCicdhdXI0tuwtxOCTI0ljKBWf40pWZx1pe7d6LmTRdXr_a"

    APP_NAME: str = "Premium Digital Store"
    SUPPORT_USERNAME: str = "@support"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SESSION_SECRET: str = "change-me-in-production"

    REDIS_URL: str = ""

    @property
    def admin_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_HOST}{self.WEBHOOK_PATH}"

    @property
    def db_url(self) -> str:
        """Return asyncpg-compatible URL regardless of what Render provides."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
