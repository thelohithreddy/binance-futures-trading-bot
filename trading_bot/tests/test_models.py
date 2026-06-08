"""Unit tests for domain models."""

from __future__ import annotations

from bot.models import OpenOrder, OrderResult


def test_order_result_from_binance_response() -> None:
    payload = {
        "orderId": 123456,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "FILLED",
        "origQty": "0.010",
        "executedQty": "0.010",
        "avgPrice": "95000.10",
        "price": "0",
        "updateTime": 1_700_000_000_000,
    }
    result = OrderResult.from_binance_response(payload)
    assert result.order_id == 123456
    assert result.status == "FILLED"
    assert str(result.executed_quantity) == "0.010"
    assert result.average_price is not None


def test_open_order_from_binance_response() -> None:
    payload = {
        "orderId": 99,
        "symbol": "BTCUSDT",
        "side": "SELL",
        "price": "100000",
        "origQty": "0.02",
        "status": "NEW",
    }
    order = OpenOrder.from_binance_response(payload)
    assert order.order_id == 99
    assert order.side == "SELL"
    assert str(order.quantity) == "0.02"
