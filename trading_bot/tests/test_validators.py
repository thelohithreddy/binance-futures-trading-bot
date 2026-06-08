"""Unit tests for order input validation."""

from __future__ import annotations

import pytest

from bot.exceptions import ValidationError
from bot.models import OrderSide, OrderType
from bot.validators import build_place_order_request, validate_symbol


def test_build_market_order_request() -> None:
    request = build_place_order_request(
        symbol="btcusdt",
        side="buy",
        order_type="market",
        quantity="0.01",
    )
    assert request.symbol == "BTCUSDT"
    assert request.side == OrderSide.BUY
    assert request.order_type == OrderType.MARKET
    assert request.price is None


def test_build_limit_order_requires_price() -> None:
    with pytest.raises(ValidationError) as exc_info:
        build_place_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.01,
        )
    assert "Price is required" in exc_info.value.details


def test_reject_non_positive_quantity() -> None:
    with pytest.raises(ValidationError):
        build_place_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0,
        )


def test_reject_invalid_side() -> None:
    with pytest.raises(ValidationError) as exc_info:
        build_place_order_request(
            symbol="BTCUSDT",
            side="HOLD",
            order_type="MARKET",
            quantity=0.01,
        )
    assert "BUY or SELL" in exc_info.value.details


def test_validate_symbol_normalizes_and_rejects_empty() -> None:
    assert validate_symbol(" ethusdt ") == "ETHUSDT"
    with pytest.raises(ValidationError):
        validate_symbol("   ")
