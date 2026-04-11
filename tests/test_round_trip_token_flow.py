import json
from pathlib import Path
import unittest
from base64 import b64decode
from datetime import datetime
from unittest.mock import patch

from fast_flights.browser_capture import _extract_first_booking_link
from fast_flights.fetcher import get_flights
from fast_flights.integrations.base import Integration
from fast_flights.parser import parse_js
from fast_flights.querying import FlightQuery, Passengers, Query, create_query


def _single_flight(
    *,
    from_code: str,
    from_name: str,
    to_code: str,
    to_name: str,
    dep_date: tuple[int, int, int],
    arr_date: tuple[int, int, int],
    dep_time: tuple[int, int],
    arr_time: tuple[int, int],
    flight_number: tuple[str, str],
):
    data = [None] * 23
    data[3] = from_code
    data[4] = from_name
    data[5] = to_name
    data[6] = to_code
    data[8] = list(dep_time)
    data[10] = list(arr_time)
    data[11] = 170
    data[17] = "Airbus A320"
    data[20] = list(dep_date)
    data[21] = list(arr_date)
    data[22] = [flight_number[0], flight_number[1], None, "Spring"]
    return data


def _flight_row(
    *,
    from_code: str,
    from_name: str,
    to_code: str,
    to_name: str,
    dep_date: tuple[int, int, int],
    arr_date: tuple[int, int, int],
    dep_time: tuple[int, int],
    arr_time: tuple[int, int],
    flight_number: tuple[str, str],
    price: int,
    token: str | None,
):
    single = _single_flight(
        from_code=from_code,
        from_name=from_name,
        to_code=to_code,
        to_name=to_name,
        dep_date=dep_date,
        arr_date=arr_date,
        dep_time=dep_time,
        arr_time=arr_time,
        flight_number=flight_number,
    )

    flight = [None] * 23
    flight[0] = "best"
    flight[1] = ["Spring"]
    flight[2] = [single]
    extras = [None] * 9
    extras[7] = 135000
    extras[8] = 140000
    flight[22] = extras

    row = [None] * 2
    row[0] = flight
    row[1] = [[None, price], token]
    return row


def _base_payload():
    payload = [None] * 8
    payload[2] = [None]
    payload[3] = [None]
    payload[7] = [None, [[["ST", "Sample Alliance"]], [["9C", "Spring"]]]]
    return payload


def _payload_js(payload: list) -> str:
    return "AF_initDataCallback({key: 'ds:1', data:" + json.dumps(payload) + ", sideChannel: {}});"


def _payload_html(payload: list) -> str:
    return "<html><body><script class='ds:1'>" + _payload_js(payload) + "</script></body></html>"


class StubIntegration(Integration):
    def __init__(self, first_html: str, second_html: str):
        self.first_html = first_html
        self.second_html = second_html
        self.booking_link_calls: list[Query] = []

    def fetch_html(self, q, /) -> str:
        if hasattr(q, "tfu") and q.tfu:
            return self.second_html
        return self.first_html

    def fetch_booking_links(self, q, results, /) -> list[str] | None:
        self.booking_link_calls.append(q)
        if len(q.flight_data) == 1 and q.selected_flight:
            return ["https://www.google.com/travel/clk/f?u=ONEWAY-FOLLOWUP"]
        if q.tfu:
            return ["https://www.google.com/travel/clk/f?u=RETURN"]
        return []


class HtmlOnlyIntegration(Integration):
    def __init__(self, html: str):
        self.html = html

    def fetch_html(self, q, /) -> str:
        return self.html


class RoundTripTokenTests(unittest.TestCase):
    def test_extract_first_booking_link_prefers_first_match(self):
        payload = (
            'https://www.google.com/travel/clk/f\\",[[\\"u\\",\\"FIRST\\"]]'
            ' some filler '
            'https://www.google.com/travel/clk/f\\",[[\\"u\\",\\"SECOND\\"]]'
        )

        self.assertEqual(
            _extract_first_booking_link(payload),
            "https://www.google.com/travel/clk/f?u=FIRST",
        )

    def test_extract_first_booking_link_from_structured_booking_response(self):
        sample_path = (
            Path(__file__).resolve().parents[2]
            / "ai-docs"
            / "booking-results-response-sample.json"
        )
        response_text = json.loads(sample_path.read_text(encoding="utf-8"))[
            "response_text"
        ]

        link = _extract_first_booking_link(response_text)

        self.assertIsNotNone(link)
        self.assertTrue(link.startswith("https://www.google.com/travel/clk/f?u="))

    def test_query_params_without_and_with_tfu(self):
        without_tfu = create_query(
            flights=[FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN")],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )
        self.assertNotIn("tfu", without_tfu.params())
        self.assertNotIn("tfu=", without_tfu.url())

        with_tfu = create_query(
            flights=[FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN")],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
            tfu="TOKEN-123",
        )
        self.assertEqual(with_tfu.params()["tfu"], "TOKEN-123")
        self.assertIn("tfu=TOKEN-123", with_tfu.url())

    def test_followup_query_can_embed_selected_outbound_fields(self):
        query = create_query(
            flights=[
                FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN"),
                FlightQuery(date=datetime(2026, 4, 5), from_airport="SGN", to_airport="CAN"),
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
            tfu="TOKEN-123",
            selected_outbound_airline_code="9C",
            selected_outbound_flight_number="7347",
        )
        raw = b64decode(query.to_str())
        # FlightData field #4 tag
        self.assertIn(bytes([0x22]), raw)
        self.assertIn(b"CAN", raw)
        self.assertIn(b"SGN", raw)
        self.assertIn(b"9C", raw)
        self.assertIn(b"7347", raw)

    def test_one_way_followup_query_can_embed_selected_flight_fields_without_tfu(self):
        query = create_query(
            flights=[FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN")],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
            selected_flight_airline_code="9C",
            selected_flight_number="7347",
        )
        raw = b64decode(query.to_str())

        self.assertIn(bytes([0x22]), raw)
        self.assertIn(b"CAN", raw)
        self.assertIn(b"SGN", raw)
        self.assertIn(b"9C", raw)
        self.assertIn(b"7347", raw)

    def test_parse_round_trip_first_response_payload_2(self):
        payload = _base_payload()
        payload[2][0] = [
            _flight_row(
                from_code="CAN",
                from_name="Guangzhou Baiyun International Airport",
                to_code="SGN",
                to_name="Tan Son Nhat International Airport",
                dep_date=(2026, 4, 1),
                arr_date=(2026, 4, 1),
                dep_time=(16, 5),
                arr_time=(17, 55),
                flight_number=("9C", "7347"),
                price=280,
                token="OUTBOUND-TOKEN",
            )
        ]
        result = parse_js(_payload_js(payload))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].price, 280)
        self.assertEqual(result[0].tfu_token, "OUTBOUND-TOKEN")
        self.assertEqual(result[0].flights[0].flight_number, "9C7347")
        self.assertEqual(result[0].flights[0].flight_number_airline_code, "9C")
        self.assertEqual(result[0].flights[0].flight_number_numeric, "7347")
        self.assertEqual(result[0].flights[0].departure.date, [2026, 4, 1])
        self.assertEqual(result[0].flights[0].departure.time, [16, 5])
        self.assertEqual(result[0].flights[0].arrival.date, [2026, 4, 1])
        self.assertEqual(result[0].flights[0].arrival.time, [17, 55])
        self.assertEqual(result[0].flights[0].duration, 170)

    def test_parse_round_trip_followup_payload_3(self):
        payload = _base_payload()
        payload[2][0] = None
        payload[3][0] = [
            [
                [
                    _flight_row(
                        from_code="SGN",
                        from_name="Tan Son Nhat International Airport",
                        to_code="CAN",
                        to_name="Guangzhou Baiyun International Airport",
                        dep_date=(2026, 4, 5),
                        arr_date=(2026, 4, 5),
                        dep_time=(18, 55),
                        arr_time=(23, 15),
                        flight_number=("9C", "7348"),
                        price=280,
                        token="RETURN-TOKEN",
                    )
                ],
                0,
                0,
                0,
                [1],
            ]
        ]
        result = parse_js(_payload_js(payload), use_payload3=True)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].tfu_token, "RETURN-TOKEN")
        self.assertEqual(result[0].flights[0].from_airport.code, "SGN")
        self.assertEqual(result[0].flights[0].to_airport.code, "CAN")
        self.assertEqual(result[0].flights[0].flight_number, "9C7348")
        self.assertEqual(result[0].flights[0].departure.date, [2026, 4, 5])
        self.assertEqual(result[0].flights[0].departure.time, [18, 55])
        self.assertEqual(result[0].flights[0].arrival.date, [2026, 4, 5])
        self.assertEqual(result[0].flights[0].arrival.time, [23, 15])
        self.assertEqual(result[0].flights[0].duration, 170)

    def test_two_step_flow_with_mocked_html(self):
        first_payload = _base_payload()
        first_payload[2][0] = [
            _flight_row(
                from_code="CAN",
                from_name="Guangzhou Baiyun International Airport",
                to_code="SGN",
                to_name="Tan Son Nhat International Airport",
                dep_date=(2026, 4, 1),
                arr_date=(2026, 4, 1),
                dep_time=(16, 5),
                arr_time=(17, 55),
                flight_number=("9C", "7347"),
                price=280,
                token="SELECTED-OUTBOUND",
            )
        ]

        second_payload = _base_payload()
        second_payload[2][0] = None
        second_payload[3][0] = [
            [
                [
                    _flight_row(
                        from_code="SGN",
                        from_name="Tan Son Nhat International Airport",
                        to_code="CAN",
                        to_name="Guangzhou Baiyun International Airport",
                        dep_date=(2026, 4, 5),
                        arr_date=(2026, 4, 5),
                        dep_time=(18, 55),
                        arr_time=(23, 15),
                        flight_number=("9C", "7348"),
                        price=280,
                        token="RETURN-TOKEN",
                    )
                ],
                0,
                0,
                0,
                [1],
            ]
        ]

        integration = StubIntegration(
            first_html=_payload_html(first_payload),
            second_html=_payload_html(second_payload),
        )

        outbound_query = create_query(
            flights=[
                FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN"),
                FlightQuery(date="2026-04-05", from_airport="SGN", to_airport="CAN"),
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )
        outbound_results = get_flights(outbound_query, integration=integration)
        self.assertEqual(outbound_results[0].tfu_token, "SELECTED-OUTBOUND")

        return_query = create_query(
            flights=[
                FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN"),
                FlightQuery(date="2026-04-05", from_airport="SGN", to_airport="CAN"),
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
            tfu=outbound_results[0].tfu_token,
        )
        return_results = get_flights(return_query, integration=integration)
        self.assertEqual(len(return_results), 1)
        self.assertEqual(return_results[0].flights[0].flight_number, "9C7348")

    def test_one_way_booking_url_is_not_added_on_initial_call(self):
        payload = _base_payload()
        payload[2][0] = [
            _flight_row(
                from_code="CAN",
                from_name="Guangzhou Baiyun International Airport",
                to_code="SGN",
                to_name="Tan Son Nhat International Airport",
                dep_date=(2026, 4, 1),
                arr_date=(2026, 4, 1),
                dep_time=(16, 5),
                arr_time=(17, 55),
                flight_number=("9C", "7347"),
                price=280,
                token=None,
            )
        ]

        integration = StubIntegration(
            first_html=_payload_html(payload),
            second_html=_payload_html(payload),
        )

        query = create_query(
            flights=[FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN")],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )
        results = get_flights(
            query,
            integration=integration,
            include_booking_urls=True,
        )

        self.assertIsNone(results[0].booking_url)
        self.assertEqual(len(integration.booking_link_calls), 0)

    def test_one_way_followup_booking_url_can_be_enriched(self):
        payload = _base_payload()
        payload[2][0] = [
            _flight_row(
                from_code="CAN",
                from_name="Guangzhou Baiyun International Airport",
                to_code="SGN",
                to_name="Tan Son Nhat International Airport",
                dep_date=(2026, 4, 1),
                arr_date=(2026, 4, 1),
                dep_time=(16, 5),
                arr_time=(17, 55),
                flight_number=("9C", "7347"),
                price=280,
                token=None,
            )
        ]

        integration = StubIntegration(
            first_html=_payload_html(payload),
            second_html=_payload_html(payload),
        )

        query = create_query(
            flights=[FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN")],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
            selected_flight_airline_code="9C",
            selected_flight_number="7347",
        )
        results = get_flights(
            query,
            integration=integration,
            include_booking_urls=True,
        )

        self.assertEqual(
            results[0].booking_url,
            "https://www.google.com/travel/clk/f?u=ONEWAY-FOLLOWUP",
        )

    def test_round_trip_booking_url_is_only_added_on_second_call(self):
        first_payload = _base_payload()
        first_payload[2][0] = [
            _flight_row(
                from_code="CAN",
                from_name="Guangzhou Baiyun International Airport",
                to_code="SGN",
                to_name="Tan Son Nhat International Airport",
                dep_date=(2026, 4, 1),
                arr_date=(2026, 4, 1),
                dep_time=(16, 5),
                arr_time=(17, 55),
                flight_number=("9C", "7347"),
                price=280,
                token="SELECTED-OUTBOUND",
            )
        ]

        second_payload = _base_payload()
        second_payload[2][0] = None
        second_payload[3][0] = [
            [
                [
                    _flight_row(
                        from_code="SGN",
                        from_name="Tan Son Nhat International Airport",
                        to_code="CAN",
                        to_name="Guangzhou Baiyun International Airport",
                        dep_date=(2026, 4, 5),
                        arr_date=(2026, 4, 5),
                        dep_time=(18, 55),
                        arr_time=(23, 15),
                        flight_number=("9C", "7348"),
                        price=280,
                        token="RETURN-TOKEN",
                    )
                ],
                0,
                0,
                0,
                [1],
            ]
        ]

        integration = StubIntegration(
            first_html=_payload_html(first_payload),
            second_html=_payload_html(second_payload),
        )

        outbound_query = create_query(
            flights=[
                FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN"),
                FlightQuery(date="2026-04-05", from_airport="SGN", to_airport="CAN"),
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
        )
        outbound_results = get_flights(
            outbound_query,
            integration=integration,
            include_booking_urls=True,
        )
        self.assertIsNone(outbound_results[0].booking_url)

        return_query = create_query(
            flights=[
                FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN"),
                FlightQuery(date="2026-04-05", from_airport="SGN", to_airport="CAN"),
            ],
            seat="economy",
            trip="round-trip",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
            tfu=outbound_results[0].tfu_token,
        )
        return_results = get_flights(
            return_query,
            integration=integration,
            include_booking_urls=True,
        )
        self.assertEqual(
            return_results[0].booking_url,
            "https://www.google.com/travel/clk/f?u=RETURN",
        )
        self.assertEqual(len(integration.booking_link_calls), 1)

    def test_playwright_fallback_only_uses_first_booking_link(self):
        payload = _base_payload()
        payload[2][0] = [
            _flight_row(
                from_code="CAN",
                from_name="Guangzhou Baiyun International Airport",
                to_code="SGN",
                to_name="Tan Son Nhat International Airport",
                dep_date=(2026, 4, 1),
                arr_date=(2026, 4, 1),
                dep_time=(16, 5),
                arr_time=(17, 55),
                flight_number=("9C", "7347"),
                price=280,
                token=None,
            )
        ]

        query = create_query(
            flights=[FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN")],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="SGD",
            selected_flight_airline_code="9C",
            selected_flight_number="7347",
        )

        async def _fake_fetch_booking_links_for_query(*args, **kwargs):
            return [
                "https://www.google.com/travel/clk/f?u=FIRST",
                "https://www.google.com/travel/clk/f?u=SECOND",
            ]

        with patch(
            "fast_flights.browser_capture.fetch_booking_links_for_query",
            side_effect=_fake_fetch_booking_links_for_query,
        ):
            results = get_flights(
                query,
                integration=HtmlOnlyIntegration(_payload_html(payload)),
                include_booking_urls=True,
            )

        self.assertEqual(
            results[0].booking_url,
            "https://www.google.com/travel/clk/f?u=FIRST",
        )


if __name__ == "__main__":
    unittest.main()
