# Implementation Progress

## Snapshot

Last reviewed: 2026-04-21

The root `flights_search` package has an implemented typed model layer, a
working request encoder, top-level API exports, and test coverage for those
pieces.

The runtime search, parser, HTTP client, and booking-resolution subsystems are
not implemented yet. They currently exist as placeholders or `NotImplemented`
API stubs.

## Current Repo Status

### Implemented

- Root package scaffold under `src/flights_search/`
- Public exports in `src/flights_search/__init__.py`
- Top-level API helpers in `src/flights_search/api.py`
- Typed request, selection, booking, and result models in
  `src/flights_search/models/core.py`
- Initial search request encoding in `src/flights_search/encoder/request.py`
- Follow-up request encoding with continuation support
- Booking request encoding for explicit selected itineraries
- Tests for models, encoder behavior, payload fixture documentation, and public
  API exports

### Present but not implemented

- `search_flights(...)`
- `get_booking_urls(...)`
- `src/flights_search/client/`
- `src/flights_search/parser/`
- `src/flights_search/booking/`

## Verification

Current test command run on 2026-04-21:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Result:

- 19 tests ran
- all tests passed

## Status By Area

### Public API

Status: partially implemented

Completed:

- public model exports are in place
- `build_booking_request(...)` returns a typed `BookingRequest`
- `get_booking_url(...)` convenience wrapper exists

Remaining:

- `search_flights(...)` runtime implementation
- `get_booking_urls(...)` runtime implementation

### Models

Status: implemented first slice

Completed:

- request models with validation
- selection models with multi-segment leg support
- booking request validation against the original search
- typed result containers
- opaque continuation handle model

Remaining:

- confirm whether any parser-only/internal helper models are still needed once
  the parser lands

### Encoder

Status: implemented first slice

Completed:

- initial request encoding
- selected-outbound follow-up encoding
- final booking request encoding
- selected-segment injection into encoded payloads

Remaining:

- validate encoded params against live retrieval behavior once the client is in
  place
- decide whether any encoder internals should be split into smaller modules as
  the subsystem grows

### Client

Status: not started

Remaining:

- choose and implement the HTTP client contract
- define retry, timeout, headers, and cookie behavior
- return retrievable Google Flights HTML for parser fixtures and runtime use

### Parser

Status: not started

Remaining:

- parse initial search payloads into `SearchResults`
- parse follow-up payloads into `SearchResults`
- attach continuation data without exposing raw transport terminology

### Booking

Status: not started

Remaining:

- implement booking-link retrieval for selected itineraries
- choose HTTP-first versus browser-assisted extraction behavior
- add booking-specific tests and fixtures

## Recommended Next Steps

1. Implement the client subsystem so encoded requests can fetch HTML fixtures
   and live pages through a stable interface.
2. Implement the parser for the committed payload fixtures and convert that into
   `search_flights(...)`.
3. Implement booking-link resolution only after the search and follow-up parse
   path is working end to end.
