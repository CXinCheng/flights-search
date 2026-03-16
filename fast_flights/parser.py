import json

from selectolax.lexbor import LexborHTMLParser

from .model import (
    Airline,
    Airport,
    Alliance,
    CarbonEmission,
    Flights,
    JsMetadata,
    SimpleDatetime,
    SingleFlight,
)


class MetaList(list[Flights]):
    """Searched flights list, with metadata attached."""

    metadata: JsMetadata


def _get_rows(payload: list, *, use_payload3: bool) -> list:
    if use_payload3:
        rows = payload[3][0]
        return rows

    rows = payload[2][0]
    return rows if rows is not None else []


def parse(html: str, *, use_payload3: bool = False) -> MetaList:
    parser = LexborHTMLParser(html)

    # find js
    script = parser.css_first(r"script.ds\:1")
    return parse_js(script.text(), use_payload3=use_payload3)


# Data discovery by @kftang, huge shout out!
def parse_js(js: str, *, use_payload3: bool = False):
    data = js.split("data:", 1)[1].rsplit(",", 1)[0]
    payload = json.loads(data)

    alliances = []
    airlines = []

    (alliances_data, airlines_data) = (
        payload[7][1][0],
        payload[7][1][1],
    )

    for code, name in alliances_data:
        alliances.append(Alliance(code=code, name=name))

    for code, name in airlines_data:
        airlines.append(Airline(code=code, name=name))

    meta = JsMetadata(alliances=alliances, airlines=airlines)

    flights = MetaList()
    rows = _get_rows(payload, use_payload3=use_payload3)
    if not rows:
        flights.metadata = meta
        return flights

    for k in rows:
        flight = k[0]
        price = k[1][0][1]
        tfu_token = k[1][1] if isinstance(k[1], list) and len(k[1]) > 1 else None

        typ = flight[0]
        airlines = flight[1]

        sg_flights = []

        # multiple flights!
        for single_flight in flight[2]:
            from_airport = Airport(code=single_flight[3], name=single_flight[4])
            to_airport = Airport(code=single_flight[6], name=single_flight[5])
            departure_time = single_flight[8]
            departure_date = single_flight[20]
            departure = SimpleDatetime(date=departure_date, time=departure_time)

            arrival_time = single_flight[10]
            arrival_date = single_flight[21]
            arrival = SimpleDatetime(date=arrival_date, time=arrival_time)

            plane_type = single_flight[17]

            duration = single_flight[11]
            raw_flight_number = single_flight[22]
            flight_number = None
            flight_number_airline_code = None
            flight_number_numeric = None
            flight_number_airline_name = None
            if (
                isinstance(raw_flight_number, list)
                and len(raw_flight_number) >= 2
                and raw_flight_number[0]
                and raw_flight_number[1]
            ):
                flight_number_airline_code = raw_flight_number[0]
                flight_number_numeric = raw_flight_number[1]
                flight_number = f"{flight_number_airline_code}{flight_number_numeric}"
                if len(raw_flight_number) >= 4 and raw_flight_number[3]:
                    flight_number_airline_name = raw_flight_number[3]

            sg_flights.append(
                SingleFlight(
                    from_airport=from_airport,
                    to_airport=to_airport,
                    departure=departure,
                    arrival=arrival,
                    duration=duration,
                    plane_type=plane_type,
                    flight_number=flight_number,
                    flight_number_airline_code=flight_number_airline_code,
                    flight_number_numeric=flight_number_numeric,
                    flight_number_airline_name=flight_number_airline_name,
                )
            )

        # some additional data
        extras = flight[22]
        carbon_emission = extras[7]
        typical_carbon_emission = extras[8]

        flights.append(
            Flights(
                type=typ,
                price=price,
                airlines=airlines,
                flights=sg_flights,
                carbon=CarbonEmission(
                    typical_on_route=typical_carbon_emission, emission=carbon_emission
                ),
                tfu_token=tfu_token,
            )
        )

    flights.metadata = meta
    return flights
