"""Unit tests for configuration."""

from __future__ import annotations

import pytest

from bot.config import Settings
from bot.exceptions import ConfigurationError


def test_validate_credentials_raises_when_missing() -> None:
    settings = Settings(
        binance_api_key="",
        binance_api_secret="",
        binance_base_url="https://testnet.binancefuture.com",
    )
    with pytest.raises(ConfigurationError) as exc_info:
        settings.validate_credentials()
    assert "BINANCE_API_KEY" in exc_info.value.details
    assert "BINANCE_API_SECRET" in exc_info.value.details


def test_futures_api_url_uses_testnet_base() -> None:
    settings = Settings(
        binance_api_key="key",
        binance_api_secret="secret",
        binance_base_url="https://testnet.binancefuture.com",
    )
    assert settings.futures_api_url == "https://testnet.binancefuture.com/fapi"
