from . import integrations

from .querying import (
    FlightQuery,
    Query,
    Passengers,
    create_query,
    create_query as create_filter,  # alias
)
from .fetcher import get_flights, fetch_flights_html

try:
    from .browser_capture import (
        BOOKING_RESULTS_URL_PART,
        capture_booking_results,
        capture_booking_results_for_query,
        fetch_booking_links,
        fetch_booking_links_for_query,
        keep_browser_open_and_capture,
    )
except ModuleNotFoundError:  # Optional Playwright dependency is missing.
    pass

__all__ = [
    "FlightQuery",
    "Query",
    "Passengers",
    "create_query",
    "create_filter",
    "get_flights",
    "fetch_flights_html",
    "integrations",
]

if "capture_booking_results" in globals():
    __all__.extend(
        [
            "BOOKING_RESULTS_URL_PART",
            "capture_booking_results",
            "capture_booking_results_for_query",
            "fetch_booking_links",
            "fetch_booking_links_for_query",
            "keep_browser_open_and_capture",
        ]
    )
