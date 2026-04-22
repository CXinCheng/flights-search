from __future__ import annotations

import sys
import types
import unittest

from flights_search.client import SearchHttpClient
from flights_search.client import http as http_module


class SearchHttpClientTests(unittest.TestCase):
    def test_fetch_search_html_retries_transient_status_codes(self) -> None:
        factory = _FakeClientFactory(
            [
                _FakeResponse(503, text="temporary outage"),
                _FakeResponse(200, text="<html>ok</html>"),
            ]
        )
        client = SearchHttpClient(max_retries=1, retry_backoff_seconds=0)

        with _patched_httpx(factory):
            html = client.fetch_search_html({"tfs": "TOKEN"})

        self.assertEqual(html, "<html>ok</html>")
        self.assertEqual(factory.calls, 2)

    def test_fetch_search_html_retries_request_errors(self) -> None:
        factory = _FakeClientFactory(
            [
                _FakeRequestError("connection dropped"),
                _FakeResponse(200, text="<html>ok</html>"),
            ]
        )
        client = SearchHttpClient(max_retries=1, retry_backoff_seconds=0)

        with _patched_httpx(factory):
            html = client.fetch_search_html({"tfs": "TOKEN"})

        self.assertEqual(html, "<html>ok</html>")
        self.assertEqual(factory.calls, 2)

    def test_fetch_search_html_persists_response_cookies_across_calls(self) -> None:
        factory = _FakeClientFactory(
            [
                _FakeResponse(
                    200,
                    text="<html>first</html>",
                    cookies={"NID": "COOKIE-123"},
                ),
                _FakeResponse(200, text="<html>second</html>"),
            ]
        )
        client = SearchHttpClient(retry_backoff_seconds=0)

        with _patched_httpx(factory):
            first_html = client.fetch_search_html({"tfs": "TOKEN-1"})
            second_html = client.fetch_booking_html({"tfs": "TOKEN-2"})

        self.assertEqual(first_html, "<html>first</html>")
        self.assertEqual(second_html, "<html>second</html>")
        self.assertEqual(factory.cookies_seen[0], {})
        self.assertEqual(factory.cookies_seen[1], {"NID": "COOKIE-123"})
        self.assertEqual(client.cookies, {"NID": "COOKIE-123"})

    def test_fetch_search_html_does_not_retry_non_retryable_status_codes(self) -> None:
        factory = _FakeClientFactory([_FakeResponse(404, text="missing")])
        client = SearchHttpClient(max_retries=3, retry_backoff_seconds=0)

        with _patched_httpx(factory) as fake_httpx:
            with self.assertRaises(fake_httpx.HTTPStatusError):
                client.fetch_search_html({"tfs": "TOKEN"})

        self.assertEqual(factory.calls, 1)

    def test_module_level_helpers_do_not_persist_cookies_across_calls(self) -> None:
        factory = _FakeClientFactory(
            [
                _FakeResponse(
                    200,
                    text="<html>first</html>",
                    cookies={"NID": "COOKIE-123"},
                ),
                _FakeResponse(200, text="<html>second</html>"),
            ]
        )

        with _patched_httpx(factory):
            first_html = http_module.fetch_search_html({"tfs": "TOKEN-1"})
            second_html = http_module.fetch_booking_html({"tfs": "TOKEN-2"})

        self.assertEqual(first_html, "<html>first</html>")
        self.assertEqual(second_html, "<html>second</html>")
        self.assertEqual(factory.cookies_seen[0], {})
        self.assertEqual(factory.cookies_seen[1], {})


class _FakeClientFactory:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls = 0
        self.cookies_seen: list[dict[str, str]] = []

    def __call__(self, **kwargs):
        cookies = kwargs.get("cookies") or {}
        self.cookies_seen.append(dict(cookies))
        return _FakeClient(self)


class _FakeClient:
    def __init__(self, factory: _FakeClientFactory) -> None:
        self._factory = factory

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def get(self, url: str, *, params: dict[str, str]) -> _FakeResponse:
        del url, params
        self._factory.calls += 1
        if not self._factory._responses:
            raise AssertionError("No fake responses remaining for httpx.Client.get().")
        response = self._factory._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FakeResponse:
    def __init__(
        self,
        status_code: int,
        *,
        text: str,
        cookies: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.cookies = _FakeCookies(cookies or {})

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise _FakeHttpStatusError(f"HTTP {self.status_code}")


class _FakeCookies:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = dict(values)

    def items(self):
        return self._values.items()


class _FakeHttpError(Exception):
    pass


class _FakeRequestError(_FakeHttpError):
    pass


class _FakeHttpStatusError(_FakeHttpError):
    pass


class _patched_httpx:
    def __init__(self, factory: _FakeClientFactory) -> None:
        self._factory = factory
        self._original = None
        self.module = types.ModuleType("httpx")
        self.module.Client = factory
        self.module.HTTPError = _FakeHttpError
        self.module.RequestError = _FakeRequestError
        self.module.HTTPStatusError = _FakeHttpStatusError

    def __enter__(self):
        self._original = sys.modules.get("httpx")
        sys.modules["httpx"] = self.module
        return self.module

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._original is None:
            sys.modules.pop("httpx", None)
        else:
            sys.modules["httpx"] = self._original
        return False


if __name__ == "__main__":
    unittest.main()
