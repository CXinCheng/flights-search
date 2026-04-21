from __future__ import annotations

import json
import unittest
from base64 import b64decode
from pathlib import Path

from flights_search.api import build_booking_request
from flights_search.encoder import (
    encode_booking_request,
    encode_follow_up_request,
    encode_search_request,
)
from flights_search.models import (
    ContinuationHandle,
    FlightSearchRequest,
    Passengers,
    SelectedItinerary,
    SelectedLeg,
    SelectedSegment,
    TripLeg,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "encoder_cases.json"


def _load_fixture_cases() -> dict[str, dict[str, object]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class EncoderTests(unittest.TestCase):
    def test_one_way_search_request_encodes_without_tfu(self) -> None:
        fixture = _load_fixture_cases()["one_way_search"]
        request = FlightSearchRequest(
            legs=(TripLeg("2026-04-01", "CAN", "SGN"),),
            trip_type="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )

        encoded = encode_search_request(request)
        raw = b64decode(encoded.params["tfs"])

        self.assertEqual(encoded.params, fixture["expected_params"])
        self.assertNotIn("tfu", encoded.params)
        self.assertEqual(encoded.params["hl"], "en-US")
        self.assertEqual(encoded.params["curr"], "SGD")
        self.assertIn(b"CAN", raw)
        self.assertIn(b"SGN", raw)

    def test_follow_up_request_embeds_selected_outbound_segments(self) -> None:
        fixture = _load_fixture_cases()["round_trip_follow_up"]
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-04-01", "CAN", "SGN"),
                TripLeg("2026-04-05", "SGN", "CAN"),
            ),
            trip_type="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )
        selected_outbound = SelectedLeg(
            segments=(
                SelectedSegment(
                    origin_airport="CAN",
                    date="2026-04-01",
                    destination_airport="SZX",
                    marketing_airline_code="CZ",
                    flight_number="123",
                ),
                SelectedSegment(
                    origin_airport="SZX",
                    date="2026-04-01",
                    destination_airport="SGN",
                    marketing_airline_code="CZ",
                    flight_number="456",
                ),
            )
        )

        encoded = encode_follow_up_request(
            request,
            continuation=ContinuationHandle("TOKEN-123"),
            selected_outbound_leg=selected_outbound,
        )
        raw = b64decode(encoded.params["tfs"])

        self.assertEqual(encoded.params, fixture["expected_params"])
        self.assertEqual(encoded.params["tfu"], "TOKEN-123")
        self.assertIn(b"CAN", raw)
        self.assertIn(b"SZX", raw)
        self.assertIn(b"SGN", raw)
        self.assertIn(b"CZ", raw)
        self.assertIn(b"123", raw)
        self.assertIn(b"456", raw)
        self.assertGreaterEqual(raw.count(bytes([0x22])), 2)

    def test_follow_up_request_requires_non_empty_continuation(self) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-04-01", "CAN", "SGN"),
                TripLeg("2026-04-05", "SGN", "CAN"),
            ),
            trip_type="round-trip",
            passengers=Passengers(adults=1),
        )
        selected_outbound = SelectedLeg(
            segments=(
                SelectedSegment(
                    origin_airport="CAN",
                    date="2026-04-01",
                    destination_airport="SGN",
                    marketing_airline_code="9C",
                    flight_number="7347",
                ),
            )
        )

        with self.assertRaises(ValueError):
            encode_follow_up_request(
                request,
                continuation=ContinuationHandle(""),
                selected_outbound_leg=selected_outbound,
            )

    def test_one_way_booking_request_embeds_selected_leg_and_omits_tfu(self) -> None:
        fixture = _load_fixture_cases()["one_way_booking"]
        request = FlightSearchRequest(
            legs=(TripLeg("2026-04-01", "CAN", "SGN"),),
            trip_type="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )
        itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="CAN",
                            date="2026-04-01",
                            destination_airport="SGN",
                            marketing_airline_code="9C",
                            flight_number="7347",
                        ),
                    )
                ),
            )
        )

        booking_request = build_booking_request(request, itinerary)
        encoded = encode_booking_request(booking_request)
        raw = b64decode(encoded.params["tfs"])

        self.assertEqual(encoded.params, fixture["expected_params"])
        self.assertNotIn("tfu", encoded.params)
        self.assertIn(b"CAN", raw)
        self.assertIn(b"SGN", raw)
        self.assertIn(b"9C", raw)
        self.assertIn(b"7347", raw)
        self.assertGreaterEqual(raw.count(bytes([0x22])), 1)

    def test_booking_request_embeds_both_legs_and_omits_tfu(self) -> None:
        fixture = _load_fixture_cases()["round_trip_booking"]
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-04-01", "CAN", "SGN"),
                TripLeg("2026-04-05", "SGN", "CAN"),
            ),
            trip_type="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )
        itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="CAN",
                            date="2026-04-01",
                            destination_airport="SGN",
                            marketing_airline_code="9C",
                            flight_number="7347",
                        ),
                    )
                ),
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="SGN",
                            date="2026-04-05",
                            destination_airport="CAN",
                            marketing_airline_code="9C",
                            flight_number="7348",
                        ),
                    )
                ),
            )
        )

        booking_request = build_booking_request(request, itinerary)
        encoded = encode_booking_request(booking_request)
        raw = b64decode(encoded.params["tfs"])

        self.assertEqual(encoded.params, fixture["expected_params"])
        self.assertNotIn("tfu", encoded.params)
        self.assertIn(b"7347", raw)
        self.assertIn(b"7348", raw)
        self.assertGreaterEqual(raw.count(bytes([0x22])), 2)


if __name__ == "__main__":
    unittest.main()
