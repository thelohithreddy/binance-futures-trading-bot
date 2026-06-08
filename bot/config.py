"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

from bot.exceptions import ConfigurationError

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Binance Futures trading bot."""

    binance_api_key: str
    binance_api_secret: str
    binance_base_url: str
    request_timeout_seconds: int = 30
    log_level: str = "INFO"
    log_file: str = "logs/trading_bot.log"

    @property
    def futures_api_url(self) -> str:
        """Base URL for USDT-M futures REST endpoints."""
        return f"{self.binance_base_url.rstrip('/')}/fapi"

    def validate_credentials(self) -> Settings:
        """Ensure API credentials are present before making requests."""
        missing: list[str] = []
        if not self.binance_api_key.strip():
            missing.append("BINANCE_API_KEY")
        if not self.binance_api_secret.strip():
            missing.append("BINANCE_API_SECRET")
        if missing:
            raise ConfigurationError(
                "Missing required API credentials.",
                details=f"Set the following environment variables: {', '.join(missing)}",
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings(
        binance_api_key=os.getenv("BINANCE_API_KEY", ""),
        binance_api_secret=os.getenv("BINANCE_API_SECRET", ""),
        binance_base_url=os.getenv(
            "BINANCE_BASE_URL",
            "https://testnet.binancefuture.com",
        ),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/trading_bot.log"),
    )
