"""
Custom application exceptions.

Raised by the service/provider layers and caught by exception handlers
registered in main.py, which convert them into proper HTTP responses.
Routes never need to know about status codes or error formatting --
that's centralized here and in main.py's handlers.
"""


class InvalidModelError(Exception):
    """Raised when a requested model is not in the supported list."""

    def __init__(self, requested_model: str, supported_models: list[str]):
        self.requested_model = requested_model
        self.supported_models = supported_models
        super().__init__(
            f"Model '{requested_model}' is not supported. "
            f"Supported models: {', '.join(supported_models)}"
        )


class ProviderTimeoutError(Exception):
    """Raised when the LLM provider does not respond within the configured timeout."""

    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"LLM provider did not respond within {timeout_seconds}s")


class ProviderRateLimitError(Exception):
    """Raised when the LLM provider reports a rate limit has been exceeded."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again shortly."):
        super().__init__(message)


class ProviderAuthenticationError(Exception):
    """Raised when the LLM provider rejects our API key."""

    def __init__(self):
        super().__init__("LLM provider rejected the API key.")


class ProviderAPIError(Exception):
    """Raised for any other provider-side failure not covered above."""

    def __init__(self, message: str = "The LLM provider returned an error."):
        super().__init__(message)


class EmptyResponseError(Exception):
    """
    Raised when the provider returns an empty response because the token
    budget was exhausted during reasoning (finish_reason == 'length' with
    no visible content). See Step 7's debugging session for context.
    """

    def __init__(self):
        super().__init__(
            "The model used its entire token budget on internal reasoning "
            "and produced no visible output. Try increasing max_tokens."
        )