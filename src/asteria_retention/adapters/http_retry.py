"""Small bounded-retry helper for public HTTP sources."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence

import httpx


TRANSIENT_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
DEFAULT_BACKOFF_SECONDS = (1.0, 2.0)


class SourceRequestError(RuntimeError):
    """Raised when a public source cannot be retrieved safely."""


def get_with_bounded_retry(
    url: str,
    *,
    source_name: str,
    timeout_seconds: float = 30.0,
    max_attempts: int = 3,
    backoff_seconds: Sequence[float] = DEFAULT_BACKOFF_SECONDS,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    """GET one URL, retrying only failures that are likely to be temporary."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if len(backoff_seconds) < max_attempts - 1:
        raise ValueError("backoff_seconds must cover every possible retry")

    with httpx.Client(
        timeout=timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": "asteria-retention-assessment/0.1"},
        transport=transport,
    ) as client:
        for attempt in range(1, max_attempts + 1):
            try:
                response = client.get(url)
            except httpx.TransportError as exc:
                if attempt == max_attempts:
                    raise SourceRequestError(
                        f"{source_name} request failed after {max_attempts} attempts: {exc}"
                    ) from exc
                sleep(float(backoff_seconds[attempt - 1]))
                continue

            if response.status_code in TRANSIENT_STATUS_CODES:
                if attempt == max_attempts:
                    raise SourceRequestError(
                        f"{source_name} request failed after {max_attempts} attempts: "
                        f"HTTP {response.status_code}"
                    )
                sleep(float(backoff_seconds[attempt - 1]))
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise SourceRequestError(
                    f"{source_name} request failed without retry: "
                    f"HTTP {response.status_code}"
                ) from exc
            return response

    raise AssertionError("bounded HTTP retry loop ended unexpectedly")
