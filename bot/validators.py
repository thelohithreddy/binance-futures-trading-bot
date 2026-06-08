"""Input validation helpers with user-friendly error messages."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from bot.exceptions import ValidationError
from bot.logging_config import get_logger
from bot.models import OrderSide, OrderType, PlaceOrderRequest

logger = get_logger(__name__, event="validation")


def _format_pydantic_errors(exc: PydanticValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()))
        message = error.get("msg", "Invalid value")
        if location:
            messages.append(f"{location}: {message}")
        else:
            messages.append(message)
    return "; ".join(messages)


def _raise_validation_error(message: str, *, details: str) -> None:
    """Log and raise a validation error."""
    logger.warning(
        "Validation failed: %s | %s",
        message,
        details,
        extra={"event": "validation_error"},
    )
    raise ValidationError(message, details=details)


def parse_decimal(value: str | float | Decimal, field_name: str) -> Decimal:
    """Parse a numeric CLI value into Decimal with a clear error on failure."""
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        _raise_validation_error(
            f"Invalid {field_name}.",
            details=f"Could not parse '{value}' as a positive number.",
        )
    if parsed <= 0:
        _raise_validation_error(
            f"Invalid {field_name}.",
            details=f"{field_name} must be greater than zero.",
        )
    return parsed


def parse_order_side(value: str) -> OrderSide:
    """Parse and validate order side."""
    normalized = value.strip().upper()
    try:
        return OrderSide(normalized)
    except ValueError:
        _raise_validation_error(
            "Invalid order side.",
            details="Side must be BUY or SELL.",
        )


def parse_order_type(value: str) -> OrderType:
    """Parse and validate order type."""
    normalized = value.strip().upper()
    try:
        return OrderType(normalized)
    except ValueError:
        _raise_validation_error(
            "Invalid order type.",
            details="Type must be MARKET or LIMIT.",
        )


def build_place_order_request(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float | Decimal,
    price: str | float | Decimal | None = None,
) -> PlaceOrderRequest:
    """
    Build and validate a place-order request from raw CLI arguments.

    Raises:
        ValidationError: When input fails schema or business validation.
    """
    if not symbol or not symbol.strip():
        _raise_validation_error(
            "Invalid symbol.",
            details="Symbol cannot be empty.",
        )

    payload: dict[str, Any] = {
        "symbol": symbol.strip().upper(),
        "side": parse_order_side(side),
        "order_type": parse_order_type(order_type),
        "quantity": parse_decimal(quantity, "quantity"),
    }

    if price is not None:
        payload["price"] = parse_decimal(price, "price")

    try:
        return PlaceOrderRequest.model_validate(payload)
    except PydanticValidationError as exc:
        details = _format_pydantic_errors(exc)
        _raise_validation_error("Order validation failed.", details=details)


def validate_symbol(symbol: str) -> str:
    """Validate a trading symbol for open-orders queries."""
    normalized = symbol.strip().upper()
    if not normalized:
        _raise_validation_error(
            "Invalid symbol.",
            details="Symbol cannot be empty.",
        )
    return normalized
