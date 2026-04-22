from __future__ import annotations

import unittest
from unittest.mock import patch

from mcp.server.fastmcp.exceptions import ToolError

from flights_search.models import (
    Airport,
    BookingRequest,
    ContinuationHandle,
    FlightOption,
    FlightSearchRequest,
    FlightSegment,
    SelectedItinerary,
    SelectedLeg,
    SelectedSegment,
    SearchResults,
    TripLeg,
)
from flights_search_mcp.server import create_server


class McpServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_lists_registered_tools(self) -> None:
        server = create_server()

        tools = await server.list_tools()

        self.assertEqual(
            {tool.name for tool in tools},
            {
                "server_info",
                "search_flights",
                "search_return_flights",
                "resolve_booking_urls",
            },
        )

    async def test_server_info_reports_metadata(self) -> None:
        server = create_server()

        _, data = await server.call_tool("server_info", {})

        self.assertEqual(data["server_name"], "flights-search-mcp")
        self.assertEqual(data["transport"], "stdio")
        self.assertIn("search_flights", data["tools"])
        self.assertIn("search_return_flights", data["tools"])
        self.assertIn("resolve_booking_urls", data["tools"])

    async def test_search_flights_tool_forwards_request_and_returns_structured_results(
        self,
    ) -> None:
        server = create_server()
        mocked_results = SearchResults(
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
                ),
            )
        )

        with patch(
            "flights_search_mcp.tools.domain_search_flights",
            return_value=mocked_results,
        ) as mock_search_flights:
            _, data = await server.call_tool(
                "search_flights",
                {
                    "trip_type": "one-way",
                    "legs": [
                        {
                            "date": "2026-06-01",
                            "origin_airport": "SFO",
                            "destination_airport": "LAX",
                        }
                    ],
                    "currency": "USD",
                },
            )

        self.assertEqual(data["selection_phase"], "initial")
        self.assertEqual(data["options"][0]["segments"][0]["date"], "2026-06-01")
        expected_request = FlightSearchRequest(
            legs=(TripLeg("2026-06-01", "SFO", "LAX"),),
            trip_type="one-way",
            currency="USD",
        )
        mock_search_flights.assert_called_once_with(expected_request)

    async def test_search_flights_tool_returns_structured_validation_errors(self) -> None:
        server = create_server()

        with self.assertRaises(ToolError) as ctx:
            await server.call_tool(
                "search_flights",
                {
                    "trip_type": "one-way",
                    "legs": [],
                },
            )

        cause = ctx.exception.__cause__
        self.assertIsNotNone(cause)
        self.assertEqual(cause.error.data["code"], "validation_error")
        self.assertFalse(cause.error.data["retryable"])

    async def test_search_return_flights_forwards_decoded_handle_and_returns_itinerary(
        self,
    ) -> None:
        server = create_server()
        mocked_results = SearchResults(
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
        outbound_selection_handle = (
            "eyJjb250aW51YXRpb25fdG9rZW4iOiJUT0tFTi0xMjMiLCJzZWxlY3RlZF9sZWciOnsic2Vn"
            "bWVudHMiOlt7ImRhdGUiOiIyMDI2LTA2LTAxIiwiZGVzdGluYXRpb25fYWlycG9ydCI6IkxB"
            "WCIsImZsaWdodF9udW1iZXIiOiIxMDAiLCJtYXJrZXRpbmdfYWlybGluZV9jb2RlIjoiVUEi"
            "LCJvcmlnaW5fYWlycG9ydCI6IlNGTyJ9XX0sInZlcnNpb24iOjF9"
        )

        with patch(
            "flights_search_mcp.tools.domain_search_follow_up_flights",
            return_value=mocked_results,
        ) as mock_search_follow_up:
            _, data = await server.call_tool(
                "search_return_flights",
                {
                    "trip_type": "round-trip",
                    "outbound_selection_handle": outbound_selection_handle,
                    "legs": [
                        {
                            "date": "2026-06-01",
                            "origin_airport": "SFO",
                            "destination_airport": "LAX",
                        },
                        {
                            "date": "2026-06-05",
                            "origin_airport": "LAX",
                            "destination_airport": "SFO",
                        },
                    ],
                },
            )

        self.assertEqual(data["selection_phase"], "follow-up")
        self.assertEqual(data["options"][0]["segments"][0]["date"], "2026-06-05")
        self.assertEqual(
            data["options"][0]["selected_itinerary"]["legs"][0]["segments"][0]["flight_number"],
            "100",
        )
        expected_request = FlightSearchRequest(
            legs=(
                TripLeg("2026-06-01", "SFO", "LAX"),
                TripLeg("2026-06-05", "LAX", "SFO"),
            ),
            trip_type="round-trip",
        )
        expected_selected_leg = SelectedLeg(
            segments=(
                SelectedSegment(
                    origin_airport="SFO",
                    date="2026-06-01",
                    destination_airport="LAX",
                    marketing_airline_code="UA",
                    flight_number="100",
                ),
            )
        )
        mock_search_follow_up.assert_called_once_with(
            expected_request,
            continuation=ContinuationHandle("TOKEN-123"),
            selected_outbound_leg=expected_selected_leg,
        )

    async def test_search_return_flights_rejects_non_round_trip_requests(self) -> None:
        server = create_server()

        with self.assertRaises(ToolError) as ctx:
            await server.call_tool(
                "search_return_flights",
                {
                    "trip_type": "one-way",
                    "outbound_selection_handle": "not-base64",
                    "legs": [
                        {
                            "date": "2026-06-01",
                            "origin_airport": "SFO",
                            "destination_airport": "LAX",
                        }
                    ],
                },
            )

        cause = ctx.exception.__cause__
        self.assertIsNotNone(cause)
        self.assertEqual(cause.error.data["code"], "unsupported_usage")
        self.assertIn("trip_type='round-trip'", cause.error.data["message"])

    async def test_resolve_booking_urls_builds_booking_request_and_returns_urls(
        self,
    ) -> None:
        server = create_server()
        expected_request = FlightSearchRequest(
            legs=(TripLeg("2026-06-01", "SFO", "LAX"),),
            trip_type="one-way",
            currency="USD",
        )
        expected_itinerary = SelectedItinerary(
            legs=(
                SelectedLeg(
                    segments=(
                        SelectedSegment(
                            origin_airport="SFO",
                            date="2026-06-01",
                            destination_airport="LAX",
                            marketing_airline_code="UA",
                            flight_number="100",
                        ),
                    )
                ),
            )
        )
        booking_request = BookingRequest(
            search_request=expected_request,
            itinerary=expected_itinerary,
        )

        with patch(
            "flights_search_mcp.tools.domain_build_booking_request",
            return_value=booking_request,
        ) as mock_build_booking_request, patch(
            "flights_search_mcp.tools.domain_get_booking_urls",
            return_value=["https://www.google.com/travel/clk/f?u=TOKEN-1"],
        ) as mock_get_booking_urls:
            _, data = await server.call_tool(
                "resolve_booking_urls",
                {
                    "trip_type": "one-way",
                    "legs": [
                        {
                            "date": "2026-06-01",
                            "origin_airport": "SFO",
                            "destination_airport": "LAX",
                        }
                    ],
                    "itinerary": {
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
                            }
                        ]
                    },
                    "currency": "USD",
                },
            )

        self.assertEqual(
            data,
            {"booking_urls": ["https://www.google.com/travel/clk/f?u=TOKEN-1"]},
        )
        mock_build_booking_request.assert_called_once_with(
            expected_request,
            expected_itinerary,
        )
        mock_get_booking_urls.assert_called_once_with(booking_request)

    async def test_resolve_booking_urls_rejects_mismatched_itinerary(self) -> None:
        server = create_server()

        with self.assertRaises(ToolError) as ctx:
            await server.call_tool(
                "resolve_booking_urls",
                {
                    "trip_type": "one-way",
                    "legs": [
                        {
                            "date": "2026-06-01",
                            "origin_airport": "SFO",
                            "destination_airport": "LAX",
                        }
                    ],
                    "itinerary": {
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
                    },
                },
            )

        cause = ctx.exception.__cause__
        self.assertIsNotNone(cause)
        self.assertEqual(cause.error.data["code"], "validation_error")
        self.assertIn("destination must match", cause.error.data["message"])

    async def test_resolve_booking_urls_maps_missing_browser_runtime_errors(self) -> None:
        server = create_server()

        with patch(
            "flights_search_mcp.tools.domain_get_booking_urls",
            side_effect=RuntimeError(
                "Missing browser binary. Run python -m playwright install chromium."
            ),
        ):
            with self.assertRaises(ToolError) as ctx:
                await server.call_tool(
                    "resolve_booking_urls",
                    {
                        "trip_type": "one-way",
                        "legs": [
                            {
                                "date": "2026-06-01",
                                "origin_airport": "SFO",
                                "destination_airport": "LAX",
                            }
                        ],
                        "itinerary": {
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
                                }
                            ]
                        },
                    },
                )

        cause = ctx.exception.__cause__
        self.assertIsNotNone(cause)
        self.assertEqual(cause.error.data["code"], "browser_runtime_missing")
        self.assertIn("playwright install chromium", cause.error.data["remediation"])

    async def test_resolve_booking_urls_maps_missing_playwright_runtime_errors(
        self,
    ) -> None:
        server = create_server()

        with patch(
            "flights_search_mcp.tools.domain_get_booking_urls",
            side_effect=RuntimeError(
                "Booking resolution requires the Playwright runtime. "
                "Install project dependencies and then run "
                "`python -m playwright install chromium`."
            ),
        ):
            with self.assertRaises(ToolError) as ctx:
                await server.call_tool(
                    "resolve_booking_urls",
                    {
                        "trip_type": "one-way",
                        "legs": [
                            {
                                "date": "2026-06-01",
                                "origin_airport": "SFO",
                                "destination_airport": "LAX",
                            }
                        ],
                        "itinerary": {
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
                                }
                            ]
                        },
                    },
                )

        cause = ctx.exception.__cause__
        self.assertIsNotNone(cause)
        self.assertEqual(cause.error.data["code"], "playwright_missing")
        self.assertIn("Install project dependencies", cause.error.data["remediation"])


if __name__ == "__main__":
    unittest.main()
