"""
IP filtering middleware for webhook security.

Validates that webhook requests come from authorized sources.
"""

import os
from ipaddress import AddressValueError, ip_address, ip_network
from typing import List

from fastapi import HTTPException, Request

# GitHub webhook IP ranges (official GitHub IPs)
# https://api.github.com/meta provides these dynamically
GITHUB_WEBHOOK_IPS = os.getenv(
    "GITHUB_WEBHOOK_IPS",
    "140.82.112.0/20,143.55.64.0/20,192.30.252.0/22,185.199.108.0/22"
).split(",")

# Enable/disable IP filtering
WEBHOOK_IP_FILTERING_ENABLED = os.getenv("WEBHOOK_IP_FILTERING_ENABLED", "false").lower() == "true"


def parse_ip_ranges(ip_ranges_str: str) -> List[str]:
    """
    Parse comma-separated IP ranges.

    Args:
        ip_ranges_str: Comma-separated IP ranges

    Returns:
        List of IP ranges
    """
    return [ip_range.strip() for ip_range in ip_ranges_str.split(",") if ip_range.strip()]


async def verify_webhook_ip(request: Request) -> bool:
    """
    Verify webhook request comes from allowed IP.

    Args:
        request: FastAPI request

    Returns:
        True if IP is allowed

    Raises:
        HTTPException: If IP is not allowed
    """
    if not WEBHOOK_IP_FILTERING_ENABLED:
        return True

    # Get client IP
    client_ip_str = request.client.host if request.client else None
    if not client_ip_str:
        raise HTTPException(
            status_code=403,
            detail="Cannot determine client IP address"
        )

    try:
        client_ip = ip_address(client_ip_str)
    except AddressValueError:
        raise HTTPException(
            status_code=403,
            detail="Invalid client IP address"
        )

    # Check if IP is in allowed ranges
    for ip_range_str in GITHUB_WEBHOOK_IPS:
        try:
            if client_ip in ip_network(ip_range_str):
                return True
        except AddressValueError:
            # Skip invalid ranges
            continue

    raise HTTPException(
        status_code=403,
        detail=f"Webhook source IP {client_ip_str} not allowed"
    )
