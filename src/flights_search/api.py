"""Top-level API surface for the greenfield package."""

from __future__ import annotations

from .models import BookingRequest, FlightSearchRequest, SearchResults, SelectedItinerary


def search_flights(request: FlightSearchRequest) -> SearchResults:
    """Search Google Flights for the provided request.

    The HTTP client and parser subsystems are not implemented in this first
    slice, so the search runtime intentionally remains a stub.
    """

    raise NotImplementedError(
        "search_flights() will be implemented after the client and parser "
        "subsystems land."
    )


def build_booking_request(
    request: FlightSearchRequest, itinerary: SelectedItinerary
) -> BookingRequest:
    """Build a typed booking request from an explicit selected itinerary."""

    return BookingRequest(search_request=request, itinerary=itinerary)


def get_booking_urls(request: BookingRequest) -> list[str]:
    """Resolve booking URL candidates for a selected itinerary.

    Booking resolution is intentionally deferred to a later subsystem slice.
    """

    raise NotImplementedError(
        "get_booking_urls() will be implemented in the booking subsystem slice."
    )


def get_booking_url(request: BookingRequest) -> str | None:
    """Convenience wrapper that returns the first booking URL, if any."""

    urls = get_booking_urls(request)
    return urls[0] if urls else None
