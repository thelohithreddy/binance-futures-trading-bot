"""CLI integration tests for error handling and graceful failures."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from decimal import Decimal

import pytest

from bot.exceptions import BinanceClientError, NetworkError, ValidationError
from bot.models import OrderSide, OrderType, PlaceOrderRequest
from cli import app


def _sample_request() -> PlaceOrderRequest:
    return PlaceOrderRequest(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.01"),
    )

runner = CliRunner()


def test_cli_invalid_side_fails_gracefully() -> None:
    result = runner.invoke(
        app,
        ["place-order", "--symbol", "BTCUSDT", "--side", "HOLD", "--type", "MARKET", "--quantity", "0.01"],
    )
    assert result.exit_code == 1
    assert "Failure" in result.stdout
    assert "BUY or SELL" in result.stdout


def test_cli_invalid_order_type_fails_gracefully() -> None:
    result = runner.invoke(
        app,
        ["place-order", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "STOP", "--quantity", "0.01"],
    )
    assert result.exit_code == 1
    assert "MARKET or LIMIT" in result.stdout


def test_cli_invalid_quantity_fails_gracefully() -> None:
    result = runner.invoke(
        app,
        ["place-order", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--quantity", "0"],
    )
    assert result.exit_code == 1
    assert "greater than zero" in result.stdout


def test_cli_limit_order_without_price_fails_gracefully() -> None:
    result = runner.invoke(
        app,
        ["place-order", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "LIMIT", "--quantity", "0.01"],
    )
    assert result.exit_code == 1
    assert "Price is required" in result.stdout


def test_cli_empty_symbol_fails_gracefully() -> None:
    result = runner.invoke(
        app,
        ["open-orders", "--symbol", "   "],
    )
    assert result.exit_code == 1
    assert "Symbol cannot be empty" in result.stdout


def test_cli_missing_credentials_fails_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)

    result = runner.invoke(
        app,
        ["open-orders", "--symbol", "BTCUSDT"],
    )

    assert result.exit_code == 1
    assert "Missing required API credentials" in result.stdout


@patch("cli.OrderService")
def test_cli_binance_api_error_fails_gracefully(mock_service_cls: MagicMock) -> None:
    service = MagicMock()
    service.prepare_order.return_value = _sample_request()
    service.execute_order.side_effect = BinanceClientError(
        "Binance API rejected the request.",
        code=-1111,
        details="Precision is over the maximum defined for this asset.",
    )
    mock_service_cls.return_value = service

    result = runner.invoke(
        app,
        ["place-order", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--quantity", "0.01"],
    )
    assert result.exit_code == 1
    assert "Binance API rejected" in result.stdout
    assert "-1111" in result.stdout


@patch("cli.OrderService")
def test_cli_network_error_fails_gracefully(mock_service_cls: MagicMock) -> None:
    service = MagicMock()
    service.prepare_order.return_value = _sample_request()
    service.execute_order.side_effect = NetworkError(
        "Unable to connect to Binance.",
        details="Connection refused",
    )
    mock_service_cls.return_value = service

    result = runner.invoke(
        app,
        ["place-order", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--quantity", "0.01"],
    )
    assert result.exit_code == 1
    assert "Unable to connect" in result.stdout


@patch("cli.OrderService")
def test_cli_validation_error_before_api_call(mock_service_cls: MagicMock) -> None:
    service = MagicMock()
    service.prepare_order.side_effect = ValidationError(
        "Invalid order side.",
        details="Side must be BUY or SELL.",
    )
    mock_service_cls.return_value = service

    result = runner.invoke(
        app,
        ["place-order", "--symbol", "BTCUSDT", "--side", "BAD", "--type", "MARKET", "--quantity", "0.01"],
    )
    assert result.exit_code == 1
    service.prepare_order.assert_called_once()
    service.execute_order.assert_not_called()
