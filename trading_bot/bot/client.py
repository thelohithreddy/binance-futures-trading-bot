"""Binance Futures API client wrapper."""

from __future__ import annotations

from typing import Any

import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.config import Settings
from bot.exceptions import BinanceClientError, NetworkError
from bot.logging_config import get_logger

logger = get_logger(__name__, event="api_client")


class BinanceFuturesClient:
    """
    Thin wrapper around python-binance for USDT-M futures operations.

    Handles authentication, request execution, and error translation so
    higher layers remain decoupled from the SDK.
    """

    def __init__(self, settings: Settings) -> None:
        settings.validate_credentials()
        self._settings = settings
        self._client = Client(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
            requests_params={"timeout": settings.request_timeout_seconds},
        )
        self._client.FUTURES_URL = settings.futures_api_url
        logger.info(
            "Initialized Binance futures client for %s",
            settings.binance_base_url,
            extra={"event": "client_init"},
        )

    def place_order(self, params: dict[str, Any]) -> dict[str, Any]:
        """Submit a new futures order."""
        return self._execute(
            operation="place_order",
            callable_=lambda: self._client.futures_create_order(**params),
            request_context={"endpoint": "POST /fapi/v1/order", "params": self._order_params_for_log(params)},
        )

    def get_open_orders(self, symbol: str) -> list[dict[str, Any]]:
        """Fetch all open orders for a symbol."""
        response = self._execute(
            operation="get_open_orders",
            callable_=lambda: self._client.futures_get_open_orders(symbol=symbol),
            request_context={
                "endpoint": "GET /fapi/v1/openOrders",
                "params": {"symbol": symbol},
            },
        )
        if isinstance(response, list):
            return response
        return []

    def _execute(
        self,
        *,
        operation: str,
        callable_: Any,
        request_context: dict[str, Any],
    ) -> Any:
        logger.info(
            "Sending API request: %s",
            request_context,
            extra={"event": f"{operation}_request"},
        )
        try:
            response = callable_()
        except BinanceAPIException as exc:
            logger.error(
                "Binance API error during %s: code=%s message=%s",
                operation,
                exc.code,
                exc.message,
                extra={"event": f"{operation}_api_error"},
            )
            raise BinanceClientError(
                "Binance API rejected the request.",
                code=exc.code,
                details=exc.message,
            ) from exc
        except BinanceRequestException as exc:
            logger.error(
                "Binance request error during %s: %s",
                operation,
                exc,
                extra={"event": f"{operation}_request_error"},
            )
            raise self._translate_request_exception(exc) from exc
        except requests.exceptions.Timeout as exc:
            logger.error(
                "Request timeout during %s after %ss",
                operation,
                self._settings.request_timeout_seconds,
                extra={"event": f"{operation}_timeout"},
            )
            raise NetworkError(
                "Request timed out while contacting Binance.",
                details=f"Timeout after {self._settings.request_timeout_seconds} seconds.",
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error(
                "Connection error during %s: %s",
                operation,
                exc,
                extra={"event": f"{operation}_connection_error"},
            )
            raise NetworkError(
                "Unable to connect to Binance.",
                details="Check your network connection and BINANCE_BASE_URL.",
            ) from exc
        except Exception as exc:
            logger.exception(
                "Unexpected error during %s",
                operation,
                extra={"event": f"{operation}_unexpected_error"},
            )
            raise

        logger.info(
            "Received API response for %s: %s",
            operation,
            self._summarize_response(response),
            extra={"event": f"{operation}_response"},
        )
        return response

    @staticmethod
    def _translate_request_exception(exc: BinanceRequestException) -> NetworkError:
        message = str(exc)
        if "timeout" in message.lower():
            return NetworkError(
                "Request timed out while contacting Binance.",
                details=message,
            )
        return NetworkError(
            "Network error while contacting Binance.",
            details=message,
        )

    @staticmethod
    def _order_params_for_log(params: dict[str, Any]) -> dict[str, Any]:
        """Return order params safe for logging (no credentials in order payloads)."""
        return {key: value for key, value in params.items()}

    @staticmethod
    def _summarize_response(response: Any) -> Any:
        if isinstance(response, dict):
            return {
                key: response.get(key)
                for key in ("orderId", "status", "executedQty", "avgPrice", "updateTime")
                if key in response
            }
        if isinstance(response, list):
            return {"count": len(response)}
        return response
