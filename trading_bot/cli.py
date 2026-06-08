"""Command-line interface for the Binance Futures trading bot."""

from __future__ import annotations

import sys
from decimal import Decimal
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bot.config import get_settings
from bot.exceptions import BinanceClientError, TradingBotError
from bot.logging_config import get_logger, setup_logging
from bot.models import OpenOrder, OrderResult, PlaceOrderRequest
from bot.orders import OrderService

app = typer.Typer(
    name="trading-bot",
    help="Binance Futures Testnet trading bot CLI.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()
logger = get_logger(__name__, event="cli")


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "—"
    normalized = value.normalize()
    return format(normalized, "f")


def _render_order_request_summary(request: PlaceOrderRequest) -> None:
    table = Table(title="Order Request Summary", show_header=False, box=None)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    table.add_row("Symbol", request.symbol)
    table.add_row("Side", request.side.value)
    table.add_row("Type", request.order_type.value)
    table.add_row("Quantity", _format_decimal(request.quantity))
    table.add_row("Price", _format_decimal(request.price))
    console.print(table)
    console.print()


def _render_order_response(result: OrderResult) -> None:
    table = Table(title="Order Response", show_header=False, box=None)
    table.add_column("Field", style="bold green")
    table.add_column("Value")
    table.add_row("Order ID", str(result.order_id))
    table.add_row("Status", result.status)
    table.add_row("Executed Quantity", _format_decimal(result.executed_quantity))
    table.add_row(
        "Average Price",
        _format_decimal(result.average_price) if result.average_price else "—",
    )
    table.add_row("Timestamp", result.timestamp.isoformat())
    console.print(table)
    console.print()


def _render_open_orders(orders: list[OpenOrder], symbol: str) -> None:
    if not orders:
        console.print(Panel(f"No open orders found for {symbol}.", style="yellow"))
        return

    table = Table(title=f"Open Orders — {symbol}")
    table.add_column("Order ID", style="cyan")
    table.add_column("Side")
    table.add_column("Price")
    table.add_column("Quantity")
    table.add_column("Status", style="green")

    for order in orders:
        table.add_row(
            str(order.order_id),
            order.side,
            _format_decimal(order.price),
            _format_decimal(order.quantity),
            order.status,
        )
    console.print(table)
    console.print()


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, TradingBotError):
        logger.error(
            "%s | details=%s",
            exc.message,
            exc.details,
            extra={"event": "cli_error"},
        )
        detail = f"\n[dim]{exc.details}[/dim]" if exc.details else ""
        if isinstance(exc, BinanceClientError) and exc.code is not None:
            detail = f"\n[dim]Binance error code: {exc.code}[/dim]{detail}"
        console.print(
            Panel(
                f"[bold red]Failure[/bold red]\n{exc.message}{detail}",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from exc

    logger.exception("Unexpected CLI error", extra={"event": "cli_unexpected_error"})
    console.print(
        Panel(
            "[bold red]Unexpected Failure[/bold red]\n"
            "An unexpected error occurred. Check logs/trading_bot.log for details.",
            border_style="red",
        )
    )
    raise typer.Exit(code=1) from exc


@app.callback()
def main() -> None:
    """Initialize logging before any command runs."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_file=settings.log_file)


@app.command("place-order")
def place_order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="Order side: BUY or SELL"),
    order_type: str = typer.Option(
        ...,
        "--type",
        "-t",
        help="Order type: MARKET or LIMIT",
    ),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: Optional[float] = typer.Option(
        None,
        "--price",
        "-p",
        help="Limit price (required for LIMIT orders)",
    ),
) -> None:
    """Place a market or limit order on Binance Futures Testnet."""
    try:
        service = OrderService()
        request = service.prepare_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        _render_order_request_summary(request)
        result = service.execute_order(request)
        _render_order_response(result)
        console.print(Panel("[bold green]Order placed successfully.[/bold green]", border_style="green"))
    except Exception as exc:
        _handle_error(exc)


@app.command("open-orders")
def open_orders(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
) -> None:
    """List open orders for a symbol."""
    try:
        service = OrderService()
        orders = service.get_open_orders(symbol=symbol)
        display_symbol = orders[0].symbol if orders else symbol.strip().upper()
        _render_open_orders(orders, display_symbol)
        console.print(
            Panel(
                f"[bold green]Retrieved {len(orders)} open order(s).[/bold green]",
                border_style="green",
            )
        )
    except Exception as exc:
        _handle_error(exc)


def run() -> None:
    """Entry point for console scripts."""
    try:
        app()
    except typer.Exit as exc:
        sys.exit(exc.exit_code)


if __name__ == "__main__":
    run()
