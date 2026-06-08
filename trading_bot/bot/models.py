"""Pydantic domain models for orders and API responses."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class PlaceOrderRequest(BaseModel):
    """Validated order placement request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: str = Field(min_length=1, description="Trading pair symbol, e.g. BTCUSDT")
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(gt=0, description="Order quantity in base asset")
    price: Decimal | None = Field(default=None, gt=0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be empty.")
        return normalized

    @model_validator(mode="after")
    def validate_limit_price(self) -> PlaceOrderRequest:
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Price is required for LIMIT orders.")
        if self.order_type == OrderType.MARKET and self.price is not None:
            raise ValueError("Price must not be set for MARKET orders.")
        return self

    def to_api_params(self) -> dict[str, Any]:
        """Convert the request into Binance futures order parameters."""
        params: dict[str, Any] = {
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.order_type.value,
            "quantity": float(self.quantity),
        }
        if self.order_type == OrderType.LIMIT:
            params["timeInForce"] = "GTC"
            params["price"] = float(self.price)  # type: ignore[arg-type]
        return params


class OrderResult(BaseModel):
    """Normalized order response from Binance."""

    order_id: int
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: Decimal
    executed_quantity: Decimal
    average_price: Decimal | None
    price: Decimal | None
    timestamp: datetime

    @classmethod
    def from_binance_response(cls, payload: dict[str, Any]) -> OrderResult:
        """Map a raw Binance futures order response to a domain model."""
        avg_price_raw = payload.get("avgPrice")
        price_raw = payload.get("price")
        update_time_ms = payload.get("updateTime") or payload.get("transactTime") or 0

        return cls(
            order_id=int(payload["orderId"]),
            symbol=str(payload.get("symbol", "")),
            side=str(payload.get("side", "")),
            order_type=str(payload.get("type", "")),
            status=str(payload.get("status", "")),
            quantity=Decimal(str(payload.get("origQty", "0"))),
            executed_quantity=Decimal(str(payload.get("executedQty", "0"))),
            average_price=(
                Decimal(str(avg_price_raw)) if avg_price_raw and float(avg_price_raw) > 0 else None
            ),
            price=(
                Decimal(str(price_raw)) if price_raw and float(price_raw) > 0 else None
            ),
            timestamp=datetime.fromtimestamp(int(update_time_ms) / 1000, tz=timezone.utc),
        )


class OpenOrder(BaseModel):
    """Normalized open order record."""

    order_id: int
    symbol: str
    side: str
    price: Decimal | None
    quantity: Decimal
    status: str

    @classmethod
    def from_binance_response(cls, payload: dict[str, Any]) -> OpenOrder:
        price_raw = payload.get("price")
        return cls(
            order_id=int(payload["orderId"]),
            symbol=str(payload.get("symbol", "")),
            side=str(payload.get("side", "")),
            price=(
                Decimal(str(price_raw)) if price_raw and float(price_raw) > 0 else None
            ),
            quantity=Decimal(str(payload.get("origQty", "0"))),
            status=str(payload.get("status", "")),
        )
