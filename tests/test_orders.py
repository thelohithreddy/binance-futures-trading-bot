"""Unit tests for the order service."""

from __future__ import annotations

from unittest.mock import MagicMock

from bot.config import Settings
from bot.orders import OrderService


def test_place_order_delegates_to_client() -> None:
    settings = Settings(
        binance_api_key="key",
        binance_api_secret="secret",
        binance_base_url="https://testnet.binancefuture.com",
    )
    client = MagicMock()
    client.place_order.return_value = {
        "orderId": 1,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "NEW",
        "origQty": "0.01",
        "executedQty": "0",
        "avgPrice": "0",
        "price": "0",
        "updateTime": 1_700_000_000_000,
    }

    service = OrderService(settings=settings, client=client)
    request, result = service.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.01,
    )

    assert request.symbol == "BTCUSDT"
    assert result.order_id == 1
    client.place_order.assert_called_once()


def test_place_order_sell_limit() -> None:
    settings = Settings(
        binance_api_key="key",
        binance_api_secret="secret",
        binance_base_url="https://testnet.binancefuture.com",
    )
    client = MagicMock()
    client.place_order.return_value = {
        "orderId": 2,
        "symbol": "ETHUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "status": "NEW",
        "origQty": "0.5",
        "executedQty": "0",
        "avgPrice": "0",
        "price": "3500",
        "updateTime": 1_700_000_000_000,
    }

    service = OrderService(settings=settings, client=client)
    request, result = service.place_order(
        symbol="ETHUSDT",
        side="SELL",
        order_type="LIMIT",
        quantity=0.5,
        price=3500,
    )

    assert request.side.value == "SELL"
    assert request.order_type.value == "LIMIT"
    assert result.order_id == 2
    params = client.place_order.call_args.args[0]
    assert params["side"] == "SELL"
    assert params["type"] == "LIMIT"
    assert params["timeInForce"] == "GTC"


def test_get_open_orders_returns_normalized_list() -> None:
    settings = Settings(
        binance_api_key="key",
        binance_api_secret="secret",
        binance_base_url="https://testnet.binancefuture.com",
    )
    client = MagicMock()
    client.get_open_orders.return_value = [
        {
            "orderId": 10,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "price": "90000",
            "origQty": "0.01",
            "status": "NEW",
        }
    ]

    service = OrderService(settings=settings, client=client)
    orders = service.get_open_orders(symbol="btcusdt")

    assert len(orders) == 1
    assert orders[0].order_id == 10
    client.get_open_orders.assert_called_once_with("BTCUSDT")
