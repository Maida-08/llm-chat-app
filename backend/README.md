# LLM Backend Service

A clean, modular FastAPI backend that wraps the Groq LLM API behind REST endpoints, built with production-oriented engineering practices: layered architecture, provider abstraction, structured logging, correlation IDs, centralized error handling, and automated tests with a mocked provider.

## Overview

This service exposes a Chat API (single-response and streaming), a Health Check, and an Available Models endpoint. All communication with Groq is isolated behind a provider abstraction, so a different LLM provider (Gemini, Claude, etc.) could be added later without changing any route or service code.

## Architecture

```
Client
  │
  ▼
FastAPI (app/main.py)
  │  ── middleware: RequestIDMiddleware attaches X-Request-ID
  ▼
Route (app/api/routes/chat.py, health.py, models.py)
  │  ── HTTP concerns only: parse request, call service, return response
  ▼
Schema validation (app/schemas/*.py)
  │  ── Pydantic: message not empty, temperature/max_tokens in range
  ▼
LLM Service (app/services/llm_service.py)
  │  ── resolves + validates model, times the call, builds response metadata
  ▼
Provider (app/providers/groq_provider.py, implements providers/base.py)
  │  ── the ONLY layer that imports the Groq SDK
  ▼
Groq API
  │
  ▼
Response flows back up: Provider → Service (adds metadata) → Route → Client
```

Each layer depends only on the abstraction below it, not the concrete implementation — most notably, `LLMService` depends on the `LLMProvider` interface (`providers/base.py`), not on `GroqProvider` directly. Swapping providers means writing one new provider class and changing one line in `app/api/dependencies.py`; no route or service code changes.

## Folder Structure

```
llm-backend-service/
├── app/
│   ├── main.py                  # FastAPI app, middleware, exception handlers
│   ├── api/
│   │   ├── routes/               # chat.py, health.py, models.py
│   │   └── dependencies.py       # dependency injection (get_llm_service)
│   ├── schemas/                  # Pydantic request/response models
│   ├── services/
│   │   └── llm_service.py        # business logic between routes and provider
│   ├── providers/
│   │   ├── base.py               # LLMProvider abstract interface
│   │   └── groq_provider.py      # Groq SDK usage lives ONLY here
│   ├── core/
│   │   ├── config.py             # environment-based settings
│   │   ├── logging.py            # structured logging + request ID filter
│   │   └── exceptions.py         # custom exception classes
│   └── utils/
│       └── timing.py             # latency measurement helper
├── tests/                        # pytest suite, mocked provider (no real API calls)
├── .env.example
├── requirements.txt
└── README.md
```

## Installation

**Prerequisites:** Python 3.10+, a Groq API key from [console.groq.com/keys](https://console.groq.com/keys).

```powershell
git clone <your-repo-url>
cd llm-backend-service
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your key:

```powershell
Copy-Item .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | Yes | — | Your Groq API key |
| `DEFAULT_MODEL` | No | `llama-3.3-70b-versatile` | Model used when a request doesn't specify one |
| `LLM_TIMEOUT` | No | `30` | Seconds to wait for a Groq response before timing out |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

`.env` is git-ignored and never committed. `.env.example` documents required variables without exposing real secrets.

## Running the Application

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

## API Endpoints

### `GET /health`
Returns service health status. No dependency on the LLM provider.

**Response:**
```json
{"status": "healthy"}
```

### `GET /api/v1/models`
Returns the list of models this service supports.

**Response:**
```json
{
  "models": [
    {"id": "llama-3.3-70b-versatile", "description": "Meta Llama 3.3 70B - versatile general-purpose model"},
    {"id": "llama-3.1-8b-instant", "description": "Meta Llama 3.1 8B - fastest, lightweight model"},
    {"id": "openai/gpt-oss-120b", "description": "OpenAI GPT-OSS 120B - open-weight reasoning model"}
  ]
}
```

### `POST /api/v1/chat`
Send a message, receive a complete response with metadata.

**Request:**
```json
{
  "message": "Write a professional email requesting a meeting.",
  "system_prompt": "You are a helpful assistant.",
  "model": "openai/gpt-oss-120b",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

Only `message` is required. `model` falls back to `DEFAULT_MODEL` if omitted.

**Response:**
```json
{
  "response": "Subject: Meeting Request...",
  "model": "openai/gpt-oss-120b",
  "tokens_used": 310,
  "latency_ms": 1420
}
```

### `POST /api/v1/chat/stream`
Same request body as `/api/v1/chat`, but streams the response as plain text chunks (`media_type: text/plain`) instead of waiting for the full completion.

All responses include an `X-Request-ID` header — a UUID correlating that request to its log lines, useful for tracing a specific request through the logs.

## Error Handling

| Scenario | Status | Error code |
|---|---|---|
| Empty/whitespace message, invalid temperature/max_tokens | 422 | Pydantic validation error |
| Unsupported model | 422 | `invalid_model` |
| Reasoning model exhausted token budget with no output | 422 | `empty_response` |
| Groq request timed out | 504 | `provider_timeout` |
| Groq rate limit exceeded | 429 | `rate_limit_exceeded` |
| Groq rejected the API key | 500 | `provider_authentication_failed` |
| Other Groq API failure | 502 | `provider_error` |
| Unexpected/unhandled exception | 500 | `internal_server_error` |

Errors are centrally translated from custom exceptions (`app/core/exceptions.py`) to HTTP responses via exception handlers in `app/main.py`. No internal details (stack traces, SDK internals, API key fragments) are ever exposed to the client.

## Provider Architecture

`app/providers/base.py` defines `LLMProvider`, an abstract interface with `chat()` and `chat_stream()` methods. `app/providers/groq_provider.py` implements it using the Groq SDK, and translates Groq-specific exceptions into this app's own exception types.

To add a new provider (e.g. Gemini):

1. Create `app/providers/gemini_provider.py`, implementing `LLMProvider`.
2. Update `app/api/dependencies.py`'s `get_llm_service()` to construct `GeminiProvider` instead of `GroqProvider`.

No changes needed anywhere in `routes/`, `services/`, or `schemas/`.

## Testing

Tests use a `FakeProvider` (see `tests/conftest.py`) injected via FastAPI's `dependency_overrides`, so **no test makes a real network call to Groq** — tests are fast, free, and deterministic.

```powershell
pytest -v
```

Covers: successful chat requests, streaming, validation failures (empty message, out-of-range temperature/max_tokens, unsupported model), health and models endpoints, and the `X-Request-ID` header.

## Logging

Structured logging via Python's `logging` module. Every log line includes the request's correlation ID (from `X-Request-ID`), timestamp, logger name, and level. Logged per chat request: model, token usage, latency, and error type on failure.

**Never logged:** API keys, message content, system prompts, or LLM response text.