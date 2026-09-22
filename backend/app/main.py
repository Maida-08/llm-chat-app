"""
Application entry point.

Creates the FastAPI app instance, wires in route modules, and registers
exception handlers that convert internal exceptions into clean HTTP
error responses.

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uuid
import contextvars

from starlette.middleware.base import BaseHTTPMiddleware
from app.api.routes import chat, health, models
from app.core.exceptions import (
    EmptyResponseError,
    InvalidModelError,
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.core.logging import configure_logging

configure_logging()
# A context variable holds the current request's ID, scoped to that single
# request's async task. This lets logger calls anywhere in the call stack
# (service layer, provider layer) access the request ID without it being
# explicitly passed down through every function signature.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generates a unique ID per request, exposes it via request_id_var,
    and echoes it back to the client in a response header."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response
    
app = FastAPI(
    title="LLM Backend Service",
    description="A production-oriented FastAPI backend wrapping Groq's LLM API.",
    version="0.1.0",
)

app.include_router(chat.router, tags=["Chat"])
app.include_router(health.router, tags=["Health"])
app.include_router(models.router, tags=["Models"])
app.add_middleware(RequestIDMiddleware)

@app.exception_handler(InvalidModelError)
async def invalid_model_handler(request: Request, exc: InvalidModelError):
    return JSONResponse(
        status_code=422,
        content={"error": "invalid_model", "message": str(exc)},
    )


@app.exception_handler(EmptyResponseError)
async def empty_response_handler(request: Request, exc: EmptyResponseError):
    return JSONResponse(
        status_code=422,
        content={"error": "empty_response", "message": str(exc)},
    )


@app.exception_handler(ProviderTimeoutError)
async def provider_timeout_handler(request: Request, exc: ProviderTimeoutError):
    return JSONResponse(
        status_code=504,
        content={"error": "provider_timeout", "message": str(exc)},
    )


@app.exception_handler(ProviderRateLimitError)
async def provider_rate_limit_handler(request: Request, exc: ProviderRateLimitError):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "message": str(exc)},
    )


@app.exception_handler(ProviderAuthenticationError)
async def provider_auth_handler(request: Request, exc: ProviderAuthenticationError):
    # Never leak details about *why* auth failed -- no key fragments, no SDK internals.
    return JSONResponse(
        status_code=500,
        content={"error": "provider_authentication_failed", "message": "The service is misconfigured. Please contact the administrator."},
    )


@app.exception_handler(ProviderAPIError)
async def provider_api_error_handler(request: Request, exc: ProviderAPIError):
    return JSONResponse(
        status_code=502,
        content={"error": "provider_error", "message": "The LLM provider returned an error. Please try again."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Last-resort catch-all. Never expose exc's raw message to the client --
    # it might contain internal paths, stack details, or SDK internals.
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred."},
    )