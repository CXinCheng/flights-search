import asyncio
from typing import overload

from primp import Client

from .integrations.base import Integration
from .pb.flights_pb2 import Trip
from .parser import MetaList, parse
from .querying import Query

URL = "https://www.google.com/travel/flights"


@overload
def get_flights(
    q: str,
    /,
    *,
    proxy: str | None = None,
    include_booking_urls: bool = False,
    booking_headless: bool = True,
    booking_timeout_ms: int = 300000,
) -> MetaList:
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(
    q: Query,
    /,
    *,
    proxy: str | None = None,
    include_booking_urls: bool = False,
    booking_headless: bool = True,
    booking_timeout_ms: int = 300000,
) -> MetaList:
    """Get flights using a structured query.

    Example:
    ```python
    get_flights(
        query(
            flights=[
                FlightQuery(
                    date="2025-12-22",
                    from_airport="TPE",
                    to_airport="MYJ",
                )
            ],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="",
        )
    )
    ```
    """


def get_flights(
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
    include_booking_urls: bool = False,
    booking_headless: bool = True,
    booking_timeout_ms: int = 300000,
) -> MetaList:
    """Get flights.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    html = fetch_flights_html(q, proxy=proxy, integration=integration)
    use_payload3 = isinstance(q, Query) and bool(q.tfu)
    results = parse(html, use_payload3=use_payload3)

    if include_booking_urls:
        _attach_booking_urls(
            results,
            q,
            integration=integration,
            booking_headless=booking_headless,
            booking_timeout_ms=booking_timeout_ms,
        )

    return results


def fetch_flights_html(
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> str:
    """Fetch flights and get the **HTML**.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    if integration is None:
        client = Client(
            impersonate="chrome_145",
            impersonate_os="macos",
            referer=True,
            proxy=proxy,
            cookie_store=True,
        )

        if isinstance(q, Query):
            params = q.params()

        else:
            params = {"q": q}

        res = client.get(URL, params=params)
        return res.text

    else:
        return integration.fetch_html(q)


def _attach_booking_urls(
    results: MetaList,
    q: Query | str,
    *,
    integration: Integration | None,
    booking_headless: bool,
    booking_timeout_ms: int,
) -> None:
    if not results or not isinstance(q, Query):
        return

    # One-way booking URLs are only valid for selected-flight follow-up calls.
    if q.trip == Trip.ONE_WAY and q.selected_flight is None:
        return

    # Round-trip booking URLs are only valid for the second-step follow-up call.
    if q.trip == Trip.ROUND_TRIP and not q.tfu:
        return

    booking_links: list[str] | None = None

    if integration is not None:
        booking_links = integration.fetch_booking_links(q, list(results))

    if booking_links is None:
        from .browser_capture import fetch_booking_links_for_query

        booking_links = asyncio.run(
            fetch_booking_links_for_query(
                q,
                headless=booking_headless,
                timeout_ms=booking_timeout_ms,
            )
        )

    for result, booking_link in zip(results, booking_links):
        result.booking_url = booking_link
