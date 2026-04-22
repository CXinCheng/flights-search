from __future__ import annotations

import json
import sys
import types
import unittest
from unittest.mock import patch

from flights_search.api import build_booking_request, get_booking_url, get_booking_urls
from flights_search.booking.browser import fetch_booking_result_texts
from flights_search.booking import extract_booking_urls
from flights_search.models import (
    FlightSearchRequest,
    SelectedItinerary,
    SelectedLeg,
    SelectedSegment,
    TripLeg,
)


class BookingExtractionTests(unittest.TestCase):
    def test_extract_booking_urls_reads_structured_response(self) -> None:
        response_text = (
            '[["ignored"], ["https://www.google.com/travel/clk/f", '
            '[["u", "TOKEN-ONE"], ["x", "1"]]], '
            '["https://www.google.com/travel/clk/f", [["u", "TOKEN-TWO"]]]]'
        )

        links = extract_booking_urls(response_text)

        self.assertEqual(
            links,
            [
                "https://www.google.com/travel/clk/f?u=TOKEN-ONE",
                "https://www.google.com/travel/clk/f?u=TOKEN-TWO",
            ],
        )

    def test_extract_booking_urls_deduplicates_structured_and_direct_links(self) -> None:
        response_text = """
        https://www.google.com/travel/clk/f?u=TOKEN-ONE
        [["https://www.google.com/travel/clk/f", [["u", "TOKEN-ONE"]]]]
        https://www.google.com/travel/clk/f?u=TOKEN-TWO
        """

        links = extract_booking_urls(response_text)

        self.assertEqual(
            links,
            [
                "https://www.google.com/travel/clk/f?u=TOKEN-ONE",
                "https://www.google.com/travel/clk/f?u=TOKEN-TWO",
            ],
        )

    def test_extract_booking_urls_preserves_pre_encoded_u_values(self) -> None:
        encoded_token = "https%3A%2F%2Fpartner.example%2Fbuy%3Fx%3D1%26y%3D2"
        response_text = (
            '[["https://www.google.com/travel/clk/f", '
            f'[["u", "{encoded_token}"]]]]'
        )

        links = extract_booking_urls(response_text)

        self.assertEqual(
            links,
            [f"https://www.google.com/travel/clk/f?u={encoded_token}"],
        )

    def test_extract_booking_urls_reads_line_framed_payloads(self) -> None:
        nested_payload = [
            ["https://www.google.com/travel/clk/f", [["u", "TOKEN-LIVE"]]]
        ]
        response_text = ")]}'\n\n42\n" + json.dumps(
            [["wrb.fr", None, json.dumps(nested_payload)]]
        )

        links = extract_booking_urls(response_text)

        self.assertEqual(
            links,
            ["https://www.google.com/travel/clk/f?u=TOKEN-LIVE"],
        )


class BookingApiTests(unittest.TestCase):
    def test_get_booking_url_returns_first_candidate(self) -> None:
        request = _make_booking_request()

        with patch(
            "flights_search.booking.google.fetch_booking_result_texts",
            return_value=[
                '[["https://www.google.com/travel/clk/f", [["u", "TOKEN-1"]]]]'
            ],
        ) as mock_fetch_booking_result_texts:
            url = get_booking_url(request)

        self.assertEqual(url, "https://www.google.com/travel/clk/f?u=TOKEN-1")
        mock_fetch_booking_result_texts.assert_called_once()
        fetch_params = mock_fetch_booking_result_texts.call_args.args[0]
        self.assertEqual(fetch_params["hl"], "en-US")
        self.assertEqual(fetch_params["curr"], "SGD")
        self.assertIn("tfs", fetch_params)
        self.assertNotIn("tfu", fetch_params)

    def test_get_booking_urls_returns_empty_list_when_links_unavailable(self) -> None:
        request = _make_booking_request()

        with patch(
            "flights_search.booking.google.fetch_booking_result_texts",
            return_value=["<html><body>unsupported shell</body></html>"],
        ):
            urls = get_booking_urls(request)

        self.assertEqual(urls, [])

    def test_get_booking_urls_propagates_fetch_failures(self) -> None:
        request = _make_booking_request()

        with patch(
            "flights_search.booking.google.fetch_booking_result_texts",
            side_effect=RuntimeError("network down"),
        ):
            with self.assertRaisesRegex(RuntimeError, "network down"):
                get_booking_urls(request)


class BookingBrowserRuntimeTests(unittest.TestCase):
    def test_fetch_booking_result_texts_reports_missing_playwright_runtime(self) -> None:
        params = {"tfs": "TOKEN", "hl": "en-US", "curr": "USD"}

        original_modules = {
            name: sys.modules.get(name)
            for name in ("playwright", "playwright.sync_api")
        }
        fake_playwright = types.ModuleType("playwright")
        sys.modules["playwright"] = fake_playwright

        try:
            with self.assertRaisesRegex(
                RuntimeError, "Install project dependencies and then run"
            ):
                fetch_booking_result_texts(params)
        finally:
            for name, module in original_modules.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_fetch_booking_result_texts_reports_missing_browser_binary(self) -> None:
        params = {"tfs": "TOKEN", "hl": "en-US", "curr": "USD"}

        class FakePlaywrightError(Exception):
            pass

        class FakeChromium:
            def launch(self, *, headless: bool):
                raise FakePlaywrightError("Executable doesn't exist at /tmp/chromium")

        class FakePlaywrightContext:
            chromium = FakeChromium()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        fake_sync_api = types.ModuleType("playwright.sync_api")
        fake_sync_api.Error = FakePlaywrightError
        fake_sync_api.sync_playwright = lambda: FakePlaywrightContext()

        original_modules = {
            name: sys.modules.get(name)
            for name in ("playwright", "playwright.sync_api")
        }
        fake_playwright = types.ModuleType("playwright")
        fake_playwright.sync_api = fake_sync_api
        sys.modules["playwright"] = fake_playwright
        sys.modules["playwright.sync_api"] = fake_sync_api

        try:
            with self.assertRaisesRegex(
                RuntimeError, "playwright install chromium"
            ):
                fetch_booking_result_texts(params)
        finally:
            for name, module in original_modules.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


def _make_booking_request():
    request = FlightSearchRequest(
        legs=(TripLeg("2026-04-01", "CAN", "SGN"),),
        trip_type="one-way",
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
    return build_booking_request(request, itinerary)


if __name__ == "__main__":
    unittest.main()
