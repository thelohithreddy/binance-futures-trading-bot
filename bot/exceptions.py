"""Domain-specific exceptions for the trading bot."""

from __future__ import annotations


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""

    def __init__(self, message: str, *, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class ConfigurationError(TradingBotError):
    """Raised when required configuration is missing or invalid."""


class ValidationError(TradingBotError):
    """Raised when user input fails business validation."""


class BinanceClientError(TradingBotError):
    """Raised when the Binance API returns an error."""

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        details: str | None = None,
    ) -> None:
        self.code = code
        super().__init__(message, details=details)


class NetworkError(TradingBotError):
    """Raised on network timeouts or connection failures."""
