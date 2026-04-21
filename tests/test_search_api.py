from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from flights_search import search_flights
from flights_search.models import FlightSearchRequest, TripLeg

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "payloads" / "one_way_initial.json"
)


def _fixture_html() -> str:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["payload"]
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
        mock_fetch_search_html.return_value = _fixture_html()

        results = search_flights(request)

        self.assertEqual(len(results.options), 1)
        self.assertEqual(results.options[0].price, 900)
        mock_fetch_search_html.assert_called_once()
        fetch_params = mock_fetch_search_html.call_args.args[0]
        self.assertEqual(fetch_params["hl"], "en-US")
        self.assertEqual(fetch_params["curr"], "SGD")
        self.assertIn("tfs", fetch_params)


if __name__ == "__main__":
    unittest.main()
