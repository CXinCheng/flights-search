from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from flights_search import search_flights, search_follow_up_flights
from flights_search.models import (
    ContinuationHandle,
    FlightSearchRequest,
    SearchResults,
    SelectedLeg,
    SelectedSegment,
    TripLeg,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "payloads"


def _fixture_html(name: str) -> str:
    payload = json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))[
        "payload"
    ]
    return (
        "<html><body>"
        f'<script class="ds:1">AF_initDataCallback({{key: "ds:1", data:'
        f"{json.dumps(payload)}"
        ", sideChannel: {}});</script>"
        "</body></html>"
    )


class SearchFlightsApiTests(unittest.TestCase):
    @patch("flights_search.api.fetch_search_html")
    def test_search_flights_encodes_request_fetches_html_and_parses_results(
        self, mock_fetch_search_html
    ) -> None:
        request = FlightSearchRequest(
            legs=(TripLeg("2026-04-01", "CAN", "SGN"),),
            trip_type="one-way",
            language="en-US",
            currency="SGD",
        )
        mock_fetch_search_html.return_value = _fixture_html("one_way_initial")

        results = search_flights(request)

        self.assertEqual(len(results.options), 1)
        self.assertEqual(results.options[0].price, 900)
        mock_fetch_search_html.assert_called_once()
        fetch_params = mock_fetch_search_html.call_args.args[0]
        self.assertEqual(fetch_params["hl"], "en-US")
        self.assertEqual(fetch_params["curr"], "SGD")
        self.assertIn("tfs", fetch_params)

    @patch("flights_search.api.fetch_search_html")
    def test_search_follow_up_flights_requests_return_options(
        self, mock_fetch_search_html
    ) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-04-01", "CAN", "SGN"),
                TripLeg("2026-04-05", "SGN", "CAN"),
            ),
            trip_type="round-trip",
            language="en-US",
            currency="SGD",
        )
        selected_outbound_leg = SelectedLeg(
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
        mock_fetch_search_html.return_value = _fixture_html("round_trip_follow_up")

        results = search_follow_up_flights(
            request,
            continuation=ContinuationHandle("TOKEN-123"),
            selected_outbound_leg=selected_outbound_leg,
        )

        self.assertEqual(results.selection_phase, "follow-up")
        self.assertEqual(len(results.options), 1)
        self.assertEqual(results.options[0].price, 1100)
        mock_fetch_search_html.assert_called_once()
        fetch_params = mock_fetch_search_html.call_args.args[0]
        self.assertEqual(fetch_params["hl"], "en-US")
        self.assertEqual(fetch_params["curr"], "SGD")
        self.assertEqual(fetch_params["tfu"], "TOKEN-123")
        self.assertIn("tfs", fetch_params)

    @patch("flights_search.api.parse_search_html")
    @patch("flights_search.api.fetch_search_html")
    def test_search_follow_up_flights_forces_follow_up_phase_when_parser_is_ambiguous(
        self, mock_fetch_search_html, mock_parse_search_html
    ) -> None:
        request = FlightSearchRequest(
            legs=(
                TripLeg("2026-04-01", "CAN", "SGN"),
                TripLeg("2026-04-05", "SGN", "CAN"),
            ),
            trip_type="round-trip",
            language="en-US",
            currency="SGD",
        )
        selected_outbound_leg = SelectedLeg(
            segments=(
                SelectedSegment(
                    origin_airport="CAN",
                    date="2026-04-01",
                    destination_airport="SGN",
                    marketing_airline_code="CZ",
                    flight_number="123",
                ),
            )
        )
        mock_fetch_search_html.return_value = "<html></html>"
        mock_parse_search_html.return_value = SearchResults(
            options=(),
            selection_phase="initial",
        )

        results = search_follow_up_flights(
            request,
            continuation=ContinuationHandle("TOKEN-123"),
            selected_outbound_leg=selected_outbound_leg,
        )

        self.assertEqual(results.selection_phase, "follow-up")
        self.assertEqual(results.options, ())


if __name__ == "__main__":
    unittest.main()
