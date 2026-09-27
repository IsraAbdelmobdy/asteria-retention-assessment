import httpx
import pytest

from asteria_retention.adapters.http_retry import (
    SourceRequestError,
    get_with_bounded_retry,
)


def test_retries_temporary_server_failure_then_succeeds():
    attempts = 0
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        status = 503 if attempts == 1 else 200
        return httpx.Response(status, request=request, content=b'{"ok": true}')

    response = get_with_bounded_retry(
        "https://example.test/data",
        source_name="Example",
        transport=httpx.MockTransport(handler),
        sleep=waits.append,
    )

    assert response.status_code == 200
    assert attempts == 2
    assert waits == [1.0]


def test_retries_transport_timeout_three_times_then_fails():
    attempts = 0
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("temporary timeout", request=request)

    with pytest.raises(SourceRequestError, match="failed after 3 attempts"):
        get_with_bounded_retry(
            "https://example.test/data",
            source_name="Example",
            transport=httpx.MockTransport(handler),
            sleep=waits.append,
        )

    assert attempts == 3
    assert waits == [1.0, 2.0]


def test_permanent_client_error_fails_without_retry():
    attempts = 0
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(404, request=request)

    with pytest.raises(SourceRequestError, match="failed without retry: HTTP 404"):
        get_with_bounded_retry(
            "https://example.test/missing",
            source_name="Example",
            transport=httpx.MockTransport(handler),
            sleep=waits.append,
        )

    assert attempts == 1
    assert waits == []


def test_rate_limit_is_retried_but_remains_bounded():
    attempts = 0
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, request=request)

    with pytest.raises(SourceRequestError, match="HTTP 429"):
        get_with_bounded_retry(
            "https://example.test/data",
            source_name="Example",
            transport=httpx.MockTransport(handler),
            sleep=waits.append,
        )

    assert attempts == 3
    assert waits == [1.0, 2.0]
