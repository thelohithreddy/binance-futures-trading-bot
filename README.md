# Binance Futures Trading Bot

A production-style Python CLI for placing and monitoring orders on **Binance USDT-M Futures Testnet**. The project emphasizes clean architecture, structured logging, robust error handling, and a clear separation between CLI, service, and exchange client layers.

## Project Overview

This bot is not a full trading platform. It is a focused, maintainable application that demonstrates how a backend engineer would structure exchange integration code: validated inputs, wrapped SDK calls, translated errors, and operator-friendly terminal output.

Supported operations:

- Place **MARKET** and **LIMIT** orders (BUY / SELL)
- List **open orders** for a symbol (bonus feature)

All trading activity targets the Binance Futures Testnet by default.

## Features

- Typer-based CLI with structured Rich terminal output
- Pydantic validation for order inputs
- Dedicated `BinanceFuturesClient` wrapper (CLI never calls SDK directly)
- `OrderService` for orchestration and response normalization
- Rotating file logs with `Timestamp | Level | Event | Details` format
- Custom exception hierarchy with user-friendly failure messages
- Unit tests for validators, models, and service logic

## Folder Structure

```text
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance SDK wrapper
│   ├── orders.py          # Order service
│   ├── validators.py      # CLI input validation
│   ├── exceptions.py      # Domain exceptions
│   ├── logging_config.py  # Logging setup
│   ├── config.py          # Environment configuration
│   └── models.py          # Pydantic domain models
├── logs/
│   └── trading_bot.log    # Created at runtime
├── tests/
├── cli.py                 # Typer CLI entry point
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

Requires **Python 3.11+** (3.10+ may work; 3.11+ recommended).

```bash
cd trading_bot
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Environment Variables

Copy the example file and add your Testnet credentials:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BINANCE_API_KEY` | Yes | — | Binance Futures Testnet API key |
| `BINANCE_API_SECRET` | Yes | — | Binance Futures Testnet API secret |
| `BINANCE_BASE_URL` | No | `https://testnet.binancefuture.com` | Futures REST base URL |
| `REQUEST_TIMEOUT_SECONDS` | No | `30` | HTTP timeout for API calls |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `LOG_FILE` | No | `logs/trading_bot.log` | Log file path |

Create Testnet API keys at: https://testnet.binancefuture.com/

## Setup Instructions

1. Create a Binance Futures Testnet account and generate API credentials.
2. Copy `.env.example` to `.env` and paste your key/secret.
3. Install dependencies from `requirements.txt`.
4. Run a command from the `trading_bot` directory.

## Example Commands

### Market Order

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit Order

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 95000
```

### Open Orders (Bonus)

```bash
python cli.py open-orders --symbol BTCUSDT
```

## Example Outputs

### Successful Market Order

```text
      Order Request Summary
 Symbol     BTCUSDT
 Side       BUY
 Type       MARKET
 Quantity   0.01
 Price      —

         Order Response
 Order ID            123456789
 Status              NEW
 Executed Quantity   0
 Average Price       —
 Timestamp           2026-06-08T12:34:56+00:00

╭────────────────────────────────────╮
│ Order placed successfully.         │
╰────────────────────────────────────╯
```

### Validation Failure

```text
╭────────────────────────────────────────────────────────╮
│ Failure                                                │
│ Order validation failed.                               │
│ Price is required for LIMIT orders.                    │
╰────────────────────────────────────────────────────────╯
```

### Open Orders

```text
                Open Orders — BTCUSDT
┏━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ Order ID ┃ Side ┃ Price   ┃ Quantity ┃ Status ┃
┡━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ 12345    │ BUY  │ 95000   │ 0.01     │ NEW    │
└──────────┴──────┴─────────┴──────────┴────────┘
```

## Logging Explanation

Logs are written to `logs/trading_bot.log` using a rotating file handler (5 MB, 3 backups).

Format:

```text
2026-06-08 12:34:56 | INFO | place_order_request | Sending API request: {...}
```

Logged events include:

- API requests and summarized responses
- Validation failures
- Binance API errors (with codes)
- Network timeouts and connection errors
- Unexpected exceptions (with stack traces)

Warnings and errors also appear on stderr for operator visibility.

## Running Tests

```bash
pytest tests/ -v
```

The suite includes **26 tests** covering validators, models, client error translation, configuration, service orchestration, and CLI graceful-failure paths.

## Assumptions

- **Testnet only by default** — `BINANCE_BASE_URL` points to Binance Futures Testnet.
- **USDT-M futures** — uses `/fapi` endpoints via `python-binance`.
- **One-way position mode** — orders do not set `positionSide`; suitable for default testnet accounts.
- **GTC limit orders** — limit orders use `timeInForce=GTC`.
- **Quantity precision** — the bot validates business rules but does not auto-adjust quantity to exchange `stepSize`; invalid precision will surface as a Binance API error.
- **Credentials via `.env`** — secrets are never hardcoded.

## Architecture Summary

```text
CLI (cli.py)
  └── OrderService (bot/orders.py)
        └── BinanceFuturesClient (bot/client.py)
              └── python-binance Client
```

Validation flows through Pydantic models (`bot/models.py`) and helper functions (`bot/validators.py`). Configuration is loaded once from the environment (`bot/config.py`).
