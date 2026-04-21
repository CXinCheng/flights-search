from __future__ import annotations

import json
import unittest
from pathlib import Path

from flights_search.parser import parse_search_html, parse_search_payload

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "payloads"


def _load_payload(name: str) -> list[object]:
    fixture = json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return fixture["payload"]


def _html_with_payload(payload: list[object]) -> str:
    return (
        "<html><head></head><body>"
        f'<script class="ds:1">AF_initDataCallback({{key: "ds:1", data:'
        f"{json.dumps(payload)}"
        ", sideChannel: {}});</script>"
        "</body></html>"
    )


class ParserTests(unittest.TestCase):
    def test_parse_initial_payload_uses_payload_two_rows(self) -> None:
        results = parse_search_payload(_load_payload("one_way_initial"))

        self.assertEqual(results.selection_phase, "initial")
        self.assertEqual(len(results.options), 1)

        option = results.options[0]
        segment = option.segments[0]

        self.assertEqual(option.kind, "best")
        self.assertEqual(option.price, 900)
        self.assertEqual(option.airlines, ("Spring",))
        self.assertIsNotNone(option.continuation)
        self.assertFalse(option.continuation.is_empty())
        self.assertIsNotNone(option.carbon)
        self.assertEqual(option.carbon.emitted_grams, 135000)
        self.assertEqual(option.carbon.typical_route_grams, 140000)
        self.assertEqual(segment.origin.code, "CAN")
        self.assertEqual(segment.origin.name, "Guangzhou")
        self.assertEqual(segment.destination.code, "SGN")
        self.assertEqual(segment.destination.name, "Ho Chi Minh City")
        self.assertEqual(segment.departure_time, "08:30")
        self.assertEqual(segment.arrival_time, "10:50")
        self.assertEqual(segment.duration_minutes, 140)
        self.assertEqual(segment.marketing_airline_code, "9C")
        self.assertEqual(segment.flight_number, "7347")
        self.assertEqual(segment.aircraft_type, "Airbus A320")

    def test_parse_follow_up_payload_uses_payload_three_rows(self) -> None:
        results = parse_search_payload(_load_payload("round_trip_follow_up"))

        self.assertEqual(results.selection_phase, "follow-up")
        self.assertEqual(len(results.options), 1)

        option = results.options[0]
        segment = option.segments[0]

        self.assertEqual(option.kind, "best")
        self.assertEqual(option.price, 1100)
        self.assertEqual(option.airlines, ("China Southern",))
        self.assertIsNotNone(option.continuation)
        self.assertEqual(segment.origin.code, "SGN")
        self.assertEqual(segment.destination.code, "CAN")
        self.assertEqual(segment.departure_time, "13:15")
        self.assertEqual(segment.arrival_time, "17:40")
        self.assertEqual(segment.duration_minutes, 265)
        self.assertEqual(segment.marketing_airline_code, "CZ")
        self.assertEqual(segment.flight_number, "456")

    def test_parse_search_html_extracts_payload_script(self) -> None:
        html = _html_with_payload(_load_payload("one_way_initial"))

        results = parse_search_html(html)

        self.assertEqual(len(results.options), 1)
        self.assertEqual(results.options[0].price, 900)

    def test_parse_search_html_requires_expected_script(self) -> None:
        with self.assertRaises(ValueError):
            parse_search_html("<html><body>No payload here.</body></html>")


if __name__ == "__main__":
    unittest.main()
