"""HTTP retrieval helpers for Google Flights search pages."""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_SEARCH_URL = "https://www.google.com/travel/flights/search"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class SearchHttpClient:
    """Minimal HTTP client for retrieving Google Flights search HTML."""

    timeout: float = DEFAULT_TIMEOUT_SECONDS
    headers: dict[str, str] = field(
        default_factory=lambda: {
            "accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "user-agent": DEFAULT_USER_AGENT,
        }
    )

    def fetch_search_html(self, params: dict[str, str]) -> str:
        """Fetch Google Flights search HTML for the encoded params."""

        import httpx

        with httpx.Client(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            response = client.get(DEFAULT_SEARCH_URL, params=params)
            response.raise_for_status()
            return response.text


def fetch_search_html(params: dict[str, str]) -> str:
    """Fetch Google Flights search HTML using the default client settings."""

    return SearchHttpClient().fetch_search_html(params)
