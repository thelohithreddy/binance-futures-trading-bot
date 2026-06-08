"""Unit tests for the Binance futures client wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests
from binance.exceptions import BinanceAPIException

from bot.client import BinanceFuturesClient
from bot.config import Settings
from bot.exceptions import BinanceClientError, ConfigurationError, NetworkError


@pytest.fixture
def settings() -> Settings:
    return Settings(
        binance_api_key="test-key",
        binance_api_secret="test-secret",
        binance_base_url="https://testnet.binancefuture.com",
    )


def test_client_raises_configuration_error_without_credentials() -> None:
    bad_settings = Settings(
        binance_api_key="",
        binance_api_secret="",
        binance_base_url="https://testnet.binancefuture.com",
    )
    with pytest.raises(ConfigurationError):
        BinanceFuturesClient(bad_settings)


@patch("bot.client.Client")
def test_place_order_translates_binance_api_error(mock_client_cls: MagicMock, settings: Settings) -> None:
    sdk_client = MagicMock()
    sdk_client.futures_create_order.side_effect = BinanceAPIException(
        response=MagicMock(),
        status_code=400,
        text='{"code":-1111,"msg":"Precision error"}',
    )
    mock_client_cls.return_value = sdk_client

    client = BinanceFuturesClient(settings)
    with pytest.raises(BinanceClientError) as exc_info:
        client.place_order({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.01})

    assert exc_info.value.code is not None
    assert sdk_client.FUTURES_URL == "https://testnet.binancefuture.com/fapi"


@patch("bot.client.Client")
def test_place_order_translates_connection_error(mock_client_cls: MagicMock, settings: Settings) -> None:
    sdk_client = MagicMock()
    sdk_client.futures_create_order.side_effect = requests.exceptions.ConnectionError("refused")
    mock_client_cls.return_value = sdk_client

    client = BinanceFuturesClient(settings)
    with pytest.raises(NetworkError) as exc_info:
        client.place_order({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.01})

    assert "connect" in exc_info.value.message.lower()


@patch("bot.client.Client")
def test_place_order_translates_timeout(mock_client_cls: MagicMock, settings: Settings) -> None:
    sdk_client = MagicMock()
    sdk_client.futures_create_order.side_effect = requests.exceptions.Timeout("timed out")
    mock_client_cls.return_value = sdk_client

    client = BinanceFuturesClient(settings)
    with pytest.raises(NetworkError):
        client.place_order({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.01})


@patch("bot.client.Client")
def test_place_order_logs_summarized_response(mock_client_cls: MagicMock, settings: Settings) -> None:
    sdk_client = MagicMock()
    sdk_client.futures_create_order.return_value = {
        "orderId": 42,
        "status": "NEW",
        "executedQty": "0",
        "avgPrice": "0",
        "updateTime": 1,
    }
    mock_client_cls.return_value = sdk_client

    client = BinanceFuturesClient(settings)
    response = client.place_order({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.01})

    assert response["orderId"] == 42
