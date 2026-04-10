# fast-flights Integration Guide

This project uses `fast_flights` to query Google Flights-style results in Python.

## Install

```bash
pip install fast-flights
```

## Core API

```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights
```

- `create_query(...)` builds the request.
- `get_flights(query)` fetches and parses results.
- Each result item includes fields like `price`, `airlines`, `flights`, `tfu_token`, and `booking_url`.

## One-way Example

```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights

query = create_query(
    flights=[
        FlightQuery(
            date="2026-04-01",
            from_airport="CAN",
            to_airport="SGN",
        )
    ],
    seat="economy",
    trip="one-way",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="SGD",
)

results = get_flights(query, include_booking_urls=True)

for i, option in enumerate(results, start=1):
    first_leg = option.flights[0]
    print(
        i,
        option.price,
        option.airlines,
        first_leg.from_airport.code,
        "->",
        first_leg.to_airport.code,
        first_leg.flight_number,
        option.booking_url,
    )
```

## Round-trip Example (2-step token flow)

For round-trip, use two calls:

1. Call once to get outbound options and collect:
- `tfu_token`
- outbound airline code (`flight_number_airline_code`)
- outbound flight number (`flight_number_numeric`)

2. Call again with those values to get return options tied to the selected outbound.

```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights

flights = [
    FlightQuery(date="2026-04-01", from_airport="CAN", to_airport="SGN"),
    FlightQuery(date="2026-04-05", from_airport="SGN", to_airport="CAN"),
]

# Step 1: outbound options
step1_query = create_query(
    flights=flights,
    seat="economy",
    trip="round-trip",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="SGD",
)
step1_results = get_flights(step1_query)

selected = step1_results[0]  # choose one option by your own logic
selected_first_leg = selected.flights[0]
selected_token = selected.tfu_token
selected_outbound_airline_code = selected_first_leg.flight_number_airline_code
selected_outbound_flight_number = selected_first_leg.flight_number_numeric

# Step 2: return options for the selected outbound
step2_query = create_query(
    flights=flights,
    seat="economy",
    trip="round-trip",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="SGD",
    tfu=selected_token,
    selected_outbound_airline_code=selected_outbound_airline_code,
    selected_outbound_flight_number=selected_outbound_flight_number,
)
step2_results = get_flights(step2_query, include_booking_urls=True)

for i, option in enumerate(step2_results, start=1):
    first_leg = option.flights[0]
    print(
        i,
        option.price,
        option.airlines,
        first_leg.from_airport.code,
        "->",
        first_leg.to_airport.code,
        first_leg.flight_number,
        option.booking_url,
    )
```

## Example Response

Below is a representative structure round-trip example outputs:

Step 1:

```python
[
    Flights(
        type="one-way",
        price=280,
        airlines=["Spring"],
        tfu_token="CjRIenBRTEllQUs4WEVBQm1WOGdCRy0tLS0tLS0tLXNtaHQxMEFBQUFBR20zeDA0TVFzaFNBEgY5QzczNDcaCwif2gEQAhoDU0dEOB1woaoB",
        flights=[
            SingleFlight(
                from_airport=Airport(code="CAN", name="Guangzhou"),
                to_airport=Airport(code="SGN", name="Ho Chi Minh City"),
                departure=SimpleDatetime(date=(2026, 4, 1), time=(16, 5)),
                arrival=SimpleDatetime(date=(2026, 4, 1), time=(17, 55)),
                duration=170,
                plane_type="Airbus A320",
                flight_number="9C7347",
                flight_number_airline_code="9C",
                flight_number_numeric="7347",
            )
        ],
    )
]
```

Step 2 (round-trip return lookup with selected token) can return entries like:

```text
price=280, airlines=['Spring'], route=SGN->CAN, flight=9C7348, booking_url=https://www.google.com/travel/clk/f?u=...
```

## Notes

- Airport values are IATA codes (for example: `CAN`, `SGN`).
- Dates use `YYYY-MM-DD`.
- `step1_results` can contain multiple outbound options; your app should decide which one to select before step 2.
- `booking_url` is available for one-way calls when you pass `include_booking_urls=True`.
- For round-trip flows, `booking_url` is only populated on the second call with `tfu=...`.


---

## Original README Content

<div align="center">

# ✈️ fast-flights (v3.0rc1)

The fast and strongly-typed Google Flights scraper (API) implemented in Python.
Based on Base64-encoded Protobuf string.

[**Documentation (v2)**](https://aweirddev.github.io/flights) • [Issues](https://github.com/AWeirdDev/flights/issues) • [PyPi (v3.0rc0)](https://pypi.org/project/fast-flights/3.0rc0/)

```haskell
$ pip install fast-flights
```

</div>

## At a glance
```python
from fast_flights import (
    FlightQuery,
    Passengers, 
    create_query, 
    get_flights
)

query = create_query(
    flights=[
        FlightQuery(
            date="YYYY-MM-DD",   # change the date
            from_airport="MYJ",  # three-letter name
            to_airport="TPE",    # three-letter name
        ),
    ],
    seat="economy",  # business/economy/first/premium-economy
    trip="one-way",  # multi-city/one-way/round-trip
    passengers=Passengers(adults=1),
    language="zh-TW",
)
res = get_flights(query)
```

## Integrations
If you'd like, you can use integrations.

Bright data:

```python
from fast_flights import get_flights
from fast_flights.integrations import BrightData

get_flights(..., integration=BrightData())
```

## What's new
- `v2.0` – New (much more succinct) API, fallback support for Playwright serverless functions, and [documentation](https://aweirddev.github.io/flights)!
- `v2.2` - Now supports **local playwright** for sending requests.
- `v3.0rc0` - Uses Javascript data instead.

## Contributing
Contributing is welcomed! A few notes though:
1. please no ai slop. i am not reading all that.
2. one change at a time. what your title says is what you've changed.
3. no new dependencies unless it's related to the core parsing.
4. really, i cant finish reading all of them, i have other projects and life to do. really sorry

***

## How it's made

The other day, I was making a chat-interface-based trip recommendation app and wanted to add a feature that can search for flights available for booking. My personal choice is definitely [Google Flights](https://flights.google.com) since Google always has the best and most organized data on the web. Therefore, I searched for APIs on Google.

> 🔎 **Search** <br />
> google flights api

The results? Bad. It seems like they discontinued this service and it now lives in the Graveyard of Google.

> <sup><a href="https://duffel.com/blog/google-flights-api" target="_blank">🧏‍♂️ <b>duffel.com</b></a></sup><br />
> <sup><i>Google Flights API: How did it work & what happened to it?</i></b>
>
> The Google Flights API offered developers access to aggregated airline data, including flight times, availability, and prices. Over a decade ago, Google announced the acquisition of ITA Software Inc. which it used to develop its API. **However, in 2018, Google ended access to the public-facing API and now only offers access through the QPX enterprise product**.

That's awful! I've also looked for free alternatives but their rate limits and pricing are just 😬 (not a good fit/deal for everyone).

<br />

However, Google Flights has their UI – [flights.google.com](https://flights.google.com). So, maybe I could just use Developer Tools to log the requests made and just replicate all of that? Undoubtedly not! Their requests are just full of numbers and unreadable text, so that's not the solution.

Perhaps, we could scrape it? I mean, Google allowed many companies like [Serpapi](https://google.com/search?q=serpapi) to scrape their web just pretending like nothing happened... So let's scrape our own.

> 🔎 **Search** <br />
> google flights ~~api~~ scraper pypi

Excluding the ones that are not active, I came across [hugoglvs/google-flights-scraper](https://pypi.org/project/google-flights-scraper) on Pypi. I thought to myself: "aint no way this is the solution!"

I checked hugoglvs's code on [GitHub](https://github.com/hugoglvs/google-flights-scraper), and I immediately detected "playwright," my worst enemy. One word can describe it well: slow. Two words? Extremely slow. What's more, it doesn't even run on the **🗻 Edge** because of configuration errors, missing libraries... etc. I could just reverse [try.playwright.tech](https://try.playwright.tech) and use a better environment, but that's just too risky if they added Cloudflare as an additional security barrier 😳.

Life tells me to never give up. Let's just take a look at their URL params...

```markdown
https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI0LTA1LTI4agcIARIDVFBFcgcIARIDTVlKGh4SCjIwMjQtMDUtMzBqBwgBEgNNWUpyBwgBEgNUUEVAAUgBcAGCAQsI____________AZgBAQ&hl=en
```

| Param | Content | My past understanding |
|-------|---------|-----------------------|
| hl    | en      | Sets the language.    |
| tfs   | CBwQAhoeEgoyMDI0LTA1LTI4agcIARID… | What is this???? 🤮🤮 |

I removed the `?tfs=` parameter and found out that this is the control of our request! And it looks so base64-y.

If we decode it to raw text, we can still see the dates, but we're not quite there — there's too much unwanted Unicode text.

Or maybe it's some kind of a **data-storing method** Google uses? What if it's something like JSON? Let's look it up.

> 🔎 **Search** <br />
> google's json alternative

> 🐣 **Result**<br />
> Solution: The Power of **Protocol Buffers**
> 
> LinkedIn turned to Protocol Buffers, often referred to as **protobuf**, a binary serialization format developed by Google. The key advantage of Protocol Buffers is its efficiency, compactness, and speed, making it significantly faster than JSON for serialization and deserialization.

Gotcha, Protobuf! Let's feed it to an online decoder and see how it does:

> 🔎 **Search** <br />
> protobuf decoder

> 🐣 **Result**<br />
> [protobuf-decoder.netlify.app](https://protobuf-decoder.netlify.app)

I then pasted the Base64-encoded string to the decoder and no way! It DID return valid data!

![annotated, Protobuf Decoder screenshot](https://github.com/AWeirdDev/flights/assets/90096971/77dfb097-f961-4494-be88-3640763dbc8c)

I immediately recognized the values — that's my data, that's my query!

So, I wrote some simple Protobuf code to decode the data.

```protobuf
syntax = "proto3"

message Airport {
    string name = 2;
}

message FlightInfo {
    string date = 2;
    Airport dep_airport = 13;
    Airport arr_airport = 14;
}

message GoogleSucks {
    repeated FlightInfo = 3;
}
```

It works! Now, I won't consider myself an "experienced Protobuf developer" but rather a complete beginner.

I have no idea what I wrote but... it worked! And here it is, `fast-flights`.

***

<div align="center">

(c) 2024-2026 AWeirdDev, and all the awesome people

</div>
