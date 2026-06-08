"""Order service for validating requests and coordinating with the API client."""

from __future__ import annotations

from bot.client import BinanceFuturesClient
from bot.config import Settings, get_settings
from bot.logging_config import get_logger
from bot.models import OpenOrder, OrderResult, PlaceOrderRequest
from bot.validators import build_place_order_request, validate_symbol

logger = get_logger(__name__, event="order_service")


class OrderService:
    """High-level service for futures order operations."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: BinanceFuturesClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client

    @property
    def client(self) -> BinanceFuturesClient:
        """Lazily initialize the API client after credentials are validated."""
        if self._client is None:
            self._settings.validate_credentials()
            self._client = BinanceFuturesClient(self._settings)
        return self._client

    def prepare_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str | float,
        price: str | float | None = None,
    ) -> PlaceOrderRequest:
        """Validate and build an order request without submitting it."""
        return build_place_order_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )

    def execute_order(self, request: PlaceOrderRequest) -> OrderResult:
        """Submit a validated order request to the exchange."""
        logger.info(
            "Placing order: symbol=%s side=%s type=%s quantity=%s price=%s",
            request.symbol,
            request.side.value,
            request.order_type.value,
            request.quantity,
            request.price,
            extra={"event": "place_order_start"},
        )
        raw_response = self.client.place_order(request.to_api_params())
        result = OrderResult.from_binance_response(raw_response)
        logger.info(
            "Order placed successfully: order_id=%s status=%s",
            result.order_id,
            result.status,
            extra={"event": "place_order_success"},
        )
        return result

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str | float,
        price: str | float | None = None,
    ) -> tuple[PlaceOrderRequest, OrderResult]:
        """Validate, submit an order, and return both request and result."""
        request = self.prepare_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        result = self.execute_order(request)
        return request, result

    def get_open_orders(self, *, symbol: str) -> list[OpenOrder]:
        """Fetch and normalize open orders for a symbol."""
        normalized_symbol = validate_symbol(symbol)
        logger.info(
            "Fetching open orders for %s",
            normalized_symbol,
            extra={"event": "open_orders_start"},
        )
        raw_orders = self.client.get_open_orders(normalized_symbol)
        orders = [OpenOrder.from_binance_response(item) for item in raw_orders]
        logger.info(
            "Retrieved %s open order(s) for %s",
            len(orders),
            normalized_symbol,
            extra={"event": "open_orders_success"},
        )
        return orders
