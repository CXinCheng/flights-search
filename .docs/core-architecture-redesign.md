# Flights Search Core Architecture Redesign

## Purpose

This document locks the greenfield architecture for the new `flights-search`
package so implementation can proceed without inheriting the legacy package
layout or reopening core API decisions.

The new package supports two product capabilities only:

1. submit a structured Google Flights search request
2. resolve booking URL candidates for a user-selected itinerary

The `legacy/` tree remains reference material for transport behavior, payload
shapes, and fixture sourcing. It does not constrain the new public API or
package structure.

## Package Layout

The root package is the active implementation surface.

```text
.
├── .docs/
├── src/
│   └── flights_search/
│       ├── __init__.py
│       ├── api.py
│       ├── booking/
│       ├── client/
│       ├── encoder/
│       ├── models/
│       ├── parser/
│       └── py.typed
├── tests/
├── pyproject.toml
└── README.md
```

Subsystem responsibilities:

- `models/`
  - owns request, response, selection, and booking-request models
  - exposes a typed public vocabulary
  - hides transport-only details behind opaque helpers or internal fields
- `encoder/`
  - converts typed requests and selections into Google Flights transport
    parameters
  - owns protobuf shape knowledge and selected-segment injection
  - contains no HTTP or HTML parsing logic
- `client/`
  - performs Google Flights retrieval with a narrow interface
  - owns headers, timeout defaults, retries, and cookie persistence decisions
- `parser/`
  - extracts typed search results from Google Flights HTML
  - owns payload indexing and normalization of raw callback data
- `booking/`
  - resolves booking links for an already selected itinerary
  - may use browser automation only inside this subsystem

## Public API

The top-level package exports a deliberately small surface:

- `FlightSearchRequest`
- `TripLeg`
- `Passengers`
- `SelectedSegment`
- `SelectedLeg`
- `SelectedItinerary`
- `SearchResults`
- `search_flights(request)`
- `build_booking_request(...)`
- `get_booking_urls(request)`
- optional convenience helper: `get_booking_url(request)`

The package does not expose:

- raw `tfs` or `tfu` values
- query-string builder utilities
- provider abstraction layers
- vendor integrations
- legacy alias terminology

## Model Boundaries

### Request models

- `TripLeg`
  - date
  - origin airport code
  - destination airport code
  - optional max stops
  - optional airline-code filter list
- `Passengers`
  - adults
  - children
  - infants in seat
  - infants on lap
- `FlightSearchRequest`
  - ordered trip legs
  - seat preference
  - trip type
  - passengers
  - language
  - currency

### Selection models

- `SelectedSegment`
  - one concrete flown segment in an itinerary
  - contains only user-meaningful fields needed to identify the segment
- `SelectedLeg`
  - ordered collection of one or more `SelectedSegment`
  - supports connecting itineraries from the start
- `SelectedItinerary`
  - ordered collection of selected legs
  - one-way itineraries contain one selected leg
  - round-trip itineraries contain two selected legs

Important design rule:

- a selected leg is not a single segment shortcut
- multi-segment support is part of the base model, not an extension

### Response models

- `Airport`
- `FlightSegment`
- `FlightOption`
- `CarbonData`
- `SearchResults`

Parser-facing raw indexing is internal to `parser/` and never appears in public
constructors.

## Continuation Handoff Design

Round-trip follow-up requires a continuation token from the outbound search
results, but the public API must not leak raw transport semantics such as
`tfu`.

Decision:

- represent continuation state as an opaque typed handle
- the handle may appear on parsed result objects and booking/search helper
  internals
- the handle does not expose Google Flights field names in the public API

Practical consequence:

- outbound search results can carry a continuation handle that is passed to the
  follow-up encoder
- callers interact with selected legs and search results, not transport fields

## Search Flow Design

### One-way flow

1. caller constructs `FlightSearchRequest`
2. `search_flights()` encodes and retrieves search HTML
3. parser returns `SearchResults`
4. caller selects a `SelectedLeg`
5. `build_booking_request()` converts the selection into a booking request
6. `get_booking_urls()` resolves zero or more booking URLs

### Round-trip flow

1. caller constructs a round-trip `FlightSearchRequest`
2. `search_flights()` returns outbound `SearchResults`
3. caller selects an outbound `SelectedLeg`
4. follow-up search uses the opaque continuation handle plus the outbound
   selection to request return options
5. parser returns return-leg `SearchResults`
6. caller selects a return `SelectedLeg`
7. `build_booking_request()` creates the final selected-itinerary request
8. `get_booking_urls()` resolves zero or more booking URLs

Clarification:

- callers do not need to issue a separate one-way search before requesting a
  round-trip search
- the initial request itself may already be `trip_type="round-trip"`
- however, the Google Flights selection flow is still two-stage in practice:
  the initial round-trip search returns outbound options first, and a follow-up
  request is required after the user selects an outbound leg

Round-trip sequence at a glance:

```text
Caller
  -> build FlightSearchRequest(trip_type="round-trip", legs=[outbound, return])
  -> search_flights(initial request)
  <- outbound SearchResults + opaque continuation handle
  -> choose outbound SelectedLeg
  -> search_flights(follow-up request using continuation + selected outbound)
  <- return SearchResults
  -> choose return SelectedLeg
  -> build_booking_request(...)
  -> get_booking_urls(...)
```

Practical interpretation:

- round-trip is a valid initial request type
- round-trip is not a single-step selection flow
- `encode_search_request(...)` covers the initial round-trip request
- `encode_follow_up_request(...)` covers the second-stage request after outbound
  selection

## Encoder Contract

The encoder provides narrow internal functions:

- encode an initial search request
- encode a follow-up request using:
  - original `FlightSearchRequest`
  - opaque continuation handle
  - selected outbound leg
- encode a booking request using:
  - original `FlightSearchRequest`
  - selected itinerary
  - optional continuation handle for round-trip completion

Encoder rules:

- protobuf usage remains internal
- selected segments are injected as ordered selections per leg
- booking requests do not include continuation params in the final booking URL
- encoder outputs transport params, not full URLs

## Client Contract

The client subsystem exposes retrieval helpers only:

- `fetch_search_html(params) -> str`
- optional booking-page retrieval helpers for HTTP-first extraction

Client rules:

- no parsing logic
- no result-model construction
- no mutation of search results

## Parser Contract

The parser owns:

- extracting Google callback payloads from HTML
- differentiating initial search payloads from follow-up payloads
- mapping raw payload data into typed `SearchResults`
- attaching opaque continuation handles where available

Parser rules:

- payload indexing stays private
- typed models are the only parser output
- parser does not perform network requests or booking resolution

## Booking Contract

Booking is an explicit operation, not a side effect of search.

Booking subsystem rules:

- accepts an explicit booking request or selected itinerary input
- returns a best-effort list of booking URLs
- may return an empty list when links are unavailable
- may use Playwright only inside `booking/`
- does not attach booking URLs onto search results by mutation

## Errors And Best-Effort Behavior

Error categories:

- model validation errors
- transport encoding errors
- client retrieval errors
- parser extraction errors
- booking resolution errors

Behavioral expectation:

- validation errors are raised eagerly
- search and booking stay separate so booking failure does not invalidate search
  results
- booking resolution is allowed to return an empty list instead of raising when
  no links are extractable

## Fixture Strategy

Fixture categories required before parser and booking work deepens:

- one-way search HTML from direct retrieval
- round-trip initial search HTML that includes continuation data
- round-trip follow-up HTML for return options
- booking-related response samples for one-way and round-trip flows
- at least one multi-segment itinerary sample if stable

Fixture rules:

- commit sanitized fixtures to the repo
- keep a small manifest documenting fixture intent and coverage
- remove session-specific or personal data where possible
- keep fixtures raw enough to detect payload regressions

## Explicit Non-Goals

The first build does not include:

- legacy compatibility shims
- generic provider abstractions
- Bright Data or other vendor integrations
- airport-enum generation
- browser-debug capture utilities in runtime code
- legacy docs carried forward unchanged

## Immediate Implementation Sequence

The next implementation steps proceed in this order:

1. bootstrap root package metadata and `pixi` tasks
2. scaffold the package and tests
3. implement request, response, selection, and booking-request models
4. implement encoder primitives and tests for:
   - one-way requests
   - round-trip requests
   - follow-up selection injection
   - multi-segment selection injection
5. capture initial fixtures before parser and booking work deepen

This document is authoritative for the first build unless scope is
intentionally reopened.
