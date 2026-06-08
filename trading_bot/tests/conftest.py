"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from bot.config import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _default_test_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide dummy credentials so CLI validation tests do not fail on config first."""
    monkeypatch.setenv("BINANCE_API_KEY", "test-key")
    monkeypatch.setenv("BINANCE_API_SECRET", "test-secret")
