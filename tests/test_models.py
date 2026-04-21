from __future__ import annotations

import unittest

from flights_search.models import (
    BookingRequest,
    ContinuationHandle,
    FlightSearchRequest,
    Passengers,
    SelectedItinerary,
    SelectedLeg,
    SelectedSegment,
    TripLeg,
)


class ModelValidationTests(unittest.TestCase):
    def test_passengers_limit_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            Passengers(adults=5, children=4, infants_in_seat=1)

    def test_infants_on_lap_require_adults(self) -> None:
        with self.assertRaises(ValueError):
            Passengers(adults=0, infants_on_lap=1)

    def test_round_trip_requests_require_two_legs(self) -> None:
        with self.assertRaises(ValueError):
            FlightSearchRequest(
                legs=(TripLeg("2026-05-01", "SFO", "JFK"),),
                trip_type="round-trip",
            )

    def test_selected_leg_requires_at_least_one_segment(self) -> None:
        with self.assertRaises(ValueError):
            SelectedLeg(segments=())

    def test_booking_request_leg_count_must_match_search_request(self) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-05-01", "SFO", "JFK"),),
            trip_type="one-way",
        )
        itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="SFO",
                            date="2026-05-01",
                            destination_airport="JFK",
                            marketing_airline_code="UA",
                            flight_number="100",
                        ),
                    )
                ),
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="JFK",
                            date="2026-05-05",
                            destination_airport="SFO",
                            marketing_airline_code="UA",
                            flight_number="101",
                        ),
                    )
                ),
            )
        )

        with self.assertRaises(ValueError):
            BookingRequest(search_request=request, itinerary=itinerary)

    def test_booking_request_leg_origin_must_match_search_request(self) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-05-01", "SFO", "JFK"),),
            trip_type="one-way",
        )
        itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="LAX",
                            date="2026-05-01",
                            destination_airport="JFK",
                            marketing_airline_code="UA",
                            flight_number="100",
                        ),
                    )
                ),
            )
        )

        with self.assertRaises(ValueError):
            BookingRequest(search_request=request, itinerary=itinerary)

    def test_booking_request_leg_date_must_match_search_request(self) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-05-01", "SFO", "JFK"),),
            trip_type="one-way",
        )
        itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="SFO",
                            date="2026-05-02",
                            destination_airport="JFK",
                            marketing_airline_code="UA",
                            flight_number="100",
                        ),
                    )
                ),
            )
        )

        with self.assertRaises(ValueError):
            BookingRequest(search_request=request, itinerary=itinerary)

    def test_booking_request_leg_destination_must_match_search_request(self) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-05-01", "SFO", "JFK"),),
            trip_type="one-way",
        )
        itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="SFO",
                            date="2026-05-01",
                            destination_airport="LAX",
                            marketing_airline_code="UA",
                            flight_number="100",
                        ),
                    )
                ),
            )
        )

        with self.assertRaises(ValueError):
            BookingRequest(search_request=request, itinerary=itinerary)

    def test_continuation_handle_is_opaque(self) -> None:
        handle = ContinuationHandle("TOKEN-123")

        self.assertFalse(handle.is_empty())


if __name__ == "__main__":
    unittest.main()
