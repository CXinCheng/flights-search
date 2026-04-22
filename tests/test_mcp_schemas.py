from __future__ import annotations

import unittest

from flights_search.models import (
    Airport,
    ContinuationHandle,
    FlightOption,
    FlightSearchRequest,
    FlightSegment,
    SearchResults,
    TripLeg,
)
from flights_search_mcp.adapters import (
    adapt_booking_urls,
    adapt_search_results,
    build_search_request,
    decode_outbound_selection_handle,
    validate_booking_request,
    validate_follow_up_request,
)
from flights_search_mcp.errors import ValidationError
from flights_search_mcp.schemas import (
    PassengersInput,
    SelectedItineraryModel,
    TripLegInput,
)


class McpAdapterTests(unittest.TestCase):
    def test_build_search_request_applies_defaults(self) -> None:
        request = build_search_request(
            legs=[TripLegInput(date="2026-06-01", origin_airport="SFO", destination_airport="LAX")],
            trip_type="one-way",
            passengers=None,
            seat="economy",
            language="en-US",
            currency="USD",
        )

        self.assertEqual(request.trip_type, "one-way")
        self.assertEqual(request.passengers.adults, 1)
        self.assertEqual(request.legs[0].date, "2026-06-01")

    def test_build_search_request_reports_domain_validation_errors(self) -> None:
        with self.assertRaises(ValidationError):
            build_search_request(
                legs=[],
                trip_type="one-way",
                passengers=PassengersInput(),
                seat="economy",
                language="en-US",
                currency="USD",
            )

    def test_adapt_search_results_derives_selected_leg_date_and_handle(self) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-06-01", "SFO", "LAX"),
                TripLeg("2026-06-05", "LAX", "SFO"),
            ),
            trip_type="round-trip",
        )
        results = SearchResults(
            options=(
                FlightOption(
                    kind="best",
                    price=120,
                    airlines=("United",),
                    segments=(
                        FlightSegment(
                            origin=Airport(code="SFO", name="San Francisco"),
                            destination=Airport(code="LAX", name="Los Angeles"),
                            departure_time="08:00",
                            arrival_time="09:30",
                            duration_minutes=90,
                            marketing_airline_code="UA",
                            flight_number="100",
                            aircraft_type="Airbus A320",
                        ),
                    ),
                    continuation=ContinuationHandle("TOKEN-123"),
                ),
            )
        )

        response = adapt_search_results(results, request)

        option = response.options[0]
        self.assertEqual(option.segments[0].date, "2026-06-01")
        self.assertIsNotNone(option.selected_leg)
        self.assertIsNotNone(option.outbound_selection_handle)

        continuation, selected_leg = decode_outbound_selection_handle(
            option.outbound_selection_handle or ""
        )
        self.assertEqual(continuation._value, "TOKEN-123")
        self.assertEqual(selected_leg.segments[0].date, "2026-06-01")
        self.assertEqual(selected_leg.segments[0].flight_number, "100")

    def test_adapt_search_results_marks_non_selectable_options(self) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-06-01", "SFO", "LAX"),),
            trip_type="one-way",
        )
        results = SearchResults(
            options=(
                FlightOption(
                    kind="best",
                    price=120,
                    airlines=("United",),
                    segments=(
                        FlightSegment(
                            origin=Airport(code="SFO", name="San Francisco"),
                            destination=Airport(code="LAX", name="Los Angeles"),
                            departure_time="08:00",
                            arrival_time="09:30",
                            duration_minutes=90,
                            marketing_airline_code="UA",
                            flight_number=None,
                            aircraft_type="Airbus A320",
                        ),
                    ),
                ),
            )
        )

        response = adapt_search_results(results, request)

        option = response.options[0]
        self.assertIsNone(option.selected_leg)
        self.assertEqual(option.selection_unavailable_reason, "missing_segment_identity")

    def test_decode_outbound_selection_handle_rejects_invalid_payloads(self) -> None:
        with self.assertRaises(ValidationError):
            decode_outbound_selection_handle("not-base64")

    def test_validate_follow_up_request_accepts_matching_round_trip_handle(self) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-06-01", "SFO", "LAX"),
                TripLeg("2026-06-05", "LAX", "SFO"),
            ),
            trip_type="round-trip",
        )
        results = SearchResults(
            options=(
                FlightOption(
                    kind="best",
                    price=120,
                    airlines=("United",),
                    segments=(
                        FlightSegment(
                            origin=Airport(code="SFO", name="San Francisco"),
                            destination=Airport(code="LAX", name="Los Angeles"),
                            departure_time="08:00",
                            arrival_time="09:30",
                            duration_minutes=90,
                            marketing_airline_code="UA",
                            flight_number="100",
                            aircraft_type="Airbus A320",
                        ),
                    ),
                    continuation=ContinuationHandle("TOKEN-123"),
                ),
            )
        )

        response = adapt_search_results(results, request)
        continuation, selected_leg = validate_follow_up_request(
            request,
            response.options[0].outbound_selection_handle or "",
        )

        self.assertEqual(continuation._value, "TOKEN-123")
        self.assertEqual(selected_leg.segments[0].origin_airport, "SFO")

    def test_validate_follow_up_request_rejects_handle_for_wrong_first_leg(self) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-06-01", "SFO", "LAX"),
                TripLeg("2026-06-05", "LAX", "SFO"),
            ),
            trip_type="round-trip",
        )
        mismatched_handle = (
            "eyJjb250aW51YXRpb25fdG9rZW4iOiJUT0tFTi0xMjMiLCJzZWxlY3RlZF9sZWciOnsic2Vn"
            "bWVudHMiOlt7ImRhdGUiOiIyMDI2LTA2LTAxIiwiZGVzdGluYXRpb25fYWlycG9ydCI6IkxB"
            "WCIsImZsaWdodF9udW1iZXIiOiIxMDAiLCJtYXJrZXRpbmdfYWlybGluZV9jb2RlIjoiVUEi"
            "LCJvcmlnaW5fYWlycG9ydCI6IkpGSyJ9XX0sInZlcnNpb24iOjF9"
        )

        with self.assertRaisesRegex(
            ValidationError,
            "origin does not match the first search leg",
        ):
            validate_follow_up_request(request, mismatched_handle)

    def test_adapt_search_results_builds_selected_itinerary_for_follow_up(self) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-06-01", "SFO", "LAX"),
                TripLeg("2026-06-05", "LAX", "SFO"),
            ),
            trip_type="round-trip",
        )
        selected_outbound_leg = decode_outbound_selection_handle(
            adapt_search_results(
                SearchResults(
                    options=(
                        FlightOption(
                            kind="best",
                            price=120,
                            airlines=("United",),
                            segments=(
                                FlightSegment(
                                    origin=Airport(code="SFO", name="San Francisco"),
                                    destination=Airport(code="LAX", name="Los Angeles"),
                                    departure_time="08:00",
                                    arrival_time="09:30",
                                    duration_minutes=90,
                                    marketing_airline_code="UA",
                                    flight_number="100",
                                    aircraft_type="Airbus A320",
                                ),
                            ),
                            continuation=ContinuationHandle("TOKEN-123"),
                        ),
                    )
                ),
                request,
            ).options[0].outbound_selection_handle
            or ""
        )[1]
        follow_up_results = SearchResults(
            options=(
                FlightOption(
                    kind="best",
                    price=140,
                    airlines=("United",),
                    segments=(
                        FlightSegment(
                            origin=Airport(code="LAX", name="Los Angeles"),
                            destination=Airport(code="SFO", name="San Francisco"),
                            departure_time="16:00",
                            arrival_time="17:30",
                            duration_minutes=90,
                            marketing_airline_code="UA",
                            flight_number="200",
                            aircraft_type="Airbus A320",
                        ),
                    ),
                ),
            ),
            selection_phase="follow-up",
        )

        response = adapt_search_results(
            follow_up_results,
            request,
            selected_outbound_leg=selected_outbound_leg,
        )

        option = response.options[0]
        self.assertEqual(option.segments[0].date, "2026-06-05")
        self.assertEqual(option.selected_itinerary.legs[0].segments[0].flight_number, "100")
        self.assertEqual(option.selected_itinerary.legs[1].segments[0].flight_number, "200")

    def test_validate_booking_request_accepts_matching_itinerary(self) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-06-01", "SFO", "LAX"),
                TripLeg("2026-06-05", "LAX", "SFO"),
            ),
            trip_type="round-trip",
        )
        itinerary = SelectedItineraryModel.model_validate(
            {
                "legs": [
                    {
                        "segments": [
                            {
                                "origin_airport": "SFO",
                                "date": "2026-06-01",
                                "destination_airport": "LAX",
                                "marketing_airline_code": "UA",
                                "flight_number": "100",
                            }
                        ]
                    },
                    {
                        "segments": [
                            {
                                "origin_airport": "LAX",
                                "date": "2026-06-05",
                                "destination_airport": "SFO",
                                "marketing_airline_code": "UA",
                                "flight_number": "200",
                            }
                        ]
                    },
                ]
            }
        )

        selected_itinerary = validate_booking_request(request, itinerary)

        self.assertEqual(len(selected_itinerary.legs), 2)
        self.assertEqual(selected_itinerary.legs[1].segments[0].flight_number, "200")

    def test_validate_booking_request_rejects_mismatched_destination(self) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-06-01", "SFO", "LAX"),),
            trip_type="one-way",
        )
        itinerary = SelectedItineraryModel.model_validate(
            {
                "legs": [
                    {
                        "segments": [
                            {
                                "origin_airport": "SFO",
                                "date": "2026-06-01",
                                "destination_airport": "JFK",
                                "marketing_airline_code": "UA",
                                "flight_number": "100",
                            }
                        ]
                    }
                ]
            }
        )

        with self.assertRaisesRegex(
            ValidationError,
            "destination must match the original search leg",
        ):
            validate_booking_request(request, itinerary)

    def test_adapt_booking_urls_returns_stable_response_shape(self) -> None:
        response = adapt_booking_urls(
            [
                "https://www.google.com/travel/clk/f?u=TOKEN-1",
                "https://www.google.com/travel/clk/f?u=TOKEN-2",
            ]
        )

        self.assertEqual(
            response.model_dump(mode="json"),
            {
                "booking_urls": [
                    "https://www.google.com/travel/clk/f?u=TOKEN-1",
                    "https://www.google.com/travel/clk/f?u=TOKEN-2",
                ]
            },
        )


if __name__ == "__main__":
    unittest.main()
