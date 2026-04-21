from __future__ import annotations

import unittest

import flights_search

from flights_search.models import FlightSearchRequest, SelectedItinerary, SelectedLeg, SelectedSegment, TripLeg


class PublicApiTests(unittest.TestCase):
    def test_top_level_exports_include_new_public_surface(self) -> None:
        self.assertTrue(hasattr(flights_search, "FlightSearchRequest"))
        self.assertTrue(hasattr(flights_search, "SelectedItinerary"))
        self.assertTrue(hasattr(flights_search, "search_flights"))
        self.assertTrue(hasattr(flights_search, "build_booking_request"))

    def test_build_booking_request_returns_typed_request(self) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-06-01", "SFO", "LAX"),),
            trip_type="one-way",
        )
        itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="SFO",
                            date="2026-06-01",
                            destination_airport="LAX",
                            marketing_airline_code="UA",
                            flight_number="1200",
                        ),
                    )
                ),
            )
        )

        booking_request = flights_search.build_booking_request(request, itinerary)

        self.assertEqual(booking_request.search_request, request)
        self.assertEqual(booking_request.itinerary, itinerary)

    def test_search_flights_is_callable(self) -> None:
        self.assertTrue(callable(flights_search.search_flights))


if __name__ == "__main__":
    unittest.main()
