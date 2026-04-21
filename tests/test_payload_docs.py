from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "payloads"


def _load_payload_fixture(name: str) -> dict[str, object]:
    path = FIXTURE_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _get_at_path(payload: object, path: list[int]) -> object:
    current = payload
    for index in path:
        current = current[index]
    return current


class PayloadDocumentationTests(unittest.TestCase):
    def test_one_way_initial_rows_live_under_payload_2(self) -> None:
        fixture = _load_payload_fixture("one_way_initial")
        payload = fixture["payload"]

        self.assertEqual(fixture["rows_path"], [2, 0])
        self.assertIsInstance(_get_at_path(payload, [2, 0]), list)
        self.assertEqual(len(_get_at_path(payload, [2, 0])), 1)
        self.assertEqual(_get_at_path(payload, [3, 0]), [])

    def test_round_trip_follow_up_rows_live_under_payload_3(self) -> None:
        fixture = _load_payload_fixture("round_trip_follow_up")
        payload = fixture["payload"]

        self.assertEqual(fixture["rows_path"], [3, 0])
        self.assertIsInstance(_get_at_path(payload, [3, 0]), list)
        self.assertEqual(len(_get_at_path(payload, [3, 0])), 1)
        self.assertEqual(_get_at_path(payload, [2, 0]), [])

    def test_metadata_location_is_shared_between_initial_and_follow_up(self) -> None:
        one_way = _load_payload_fixture("one_way_initial")
        follow_up = _load_payload_fixture("round_trip_follow_up")

        self.assertEqual(one_way["airlines_path"], [7, 1, 1])
        self.assertEqual(one_way["alliances_path"], [7, 1, 0])
        self.assertEqual(follow_up["airlines_path"], [7, 1, 1])
        self.assertEqual(follow_up["alliances_path"], [7, 1, 0])
        self.assertEqual(_get_at_path(one_way["payload"], [7, 1, 1, 0]), ["9C", "Spring"])
        self.assertEqual(
            _get_at_path(follow_up["payload"], [7, 1, 1, 0]),
            ["CZ", "China Southern"],
        )


if __name__ == "__main__":
    unittest.main()
