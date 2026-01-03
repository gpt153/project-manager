"""
Rate limiting middleware using slowapi.

Protects API endpoints from abuse and DoS attacks.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response


# Create limiter instance with configurable default limits
DEFAULT_RATE_LIMIT = os.getenv("DEFAULT_RATE_LIMIT", "100/minute")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_RATE_LIMIT],
    storage_uri="memory://"  # Can be changed to redis:// for distributed systems
)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom error handler for rate limit exceeded.

    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception

    Returns:
        JSON response with 429 status code
    """
    return Response(
        content='{"error": "Rate limit exceeded", "detail": "Too many requests. Please try again later."}',
        status_code=429,
        media_type="application/json",
        headers={"Retry-After": str(exc.detail)}
    )
