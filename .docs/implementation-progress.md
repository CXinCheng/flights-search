# Implementation Progress

## Snapshot

Last reviewed: 2026-04-21

The root `flights_search` package has an implemented typed model layer, a
working request encoder, a basic HTTP client, HTML/payload parser support,
top-level API exports, and test coverage for those pieces.

The runtime booking-resolution subsystem is still not implemented. The public
runtime API also does not yet expose the round-trip follow-up search step.

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
- HTTP retrieval helper in `src/flights_search/client/`
- HTML and payload parsing in `src/flights_search/parser/`
- `search_flights(...)` wired through encoder + client + parser
- Tests for models, encoder behavior, parser behavior, payload fixture
  documentation, search API wiring, and public API exports

### Present but not implemented

- `get_booking_urls(...)`
- `src/flights_search/booking/`
- public follow-up search helper for round-trip selection flow

## Verification

Current test command run on 2026-04-21:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Result:

- 25 tests ran
- all tests passed

## Status By Area

### Public API

Status: implemented first runtime slice

Completed:

- public model exports are in place
- `search_flights(...)` executes the initial search runtime path
- `build_booking_request(...)` returns a typed `BookingRequest`
- `get_booking_url(...)` convenience wrapper exists

Remaining:

- `get_booking_urls(...)` runtime implementation
- explicit public follow-up search API for round-trip outbound selection

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

Status: implemented first slice

Remaining:

- decide whether to add retries and cookie persistence on top of the current
  `httpx` retrieval helper
- validate the current headers and timeout choices against stable live
  retrieval behavior once environment access is available

### Parser

Status: implemented first slice

Remaining:

- expand beyond the committed synthetic payload shapes
- validate parser behavior against stable live HTML fixtures
- decide whether airline/alliance metadata should remain internal-only or gain
  a typed surface later

### Booking

Status: not started

Remaining:

- implement booking-link retrieval for selected itineraries
- choose HTTP-first versus browser-assisted extraction behavior
- add booking-specific tests and fixtures

## Recommended Next Steps

1. Add a public follow-up round-trip helper that accepts the outbound
   selection plus continuation handle and returns return-leg `SearchResults`.
2. Validate the client/parser path against real captured HTML fixtures once a
   stable retrieval setup is available.
3. Implement booking-link resolution only after the search and follow-up path
   is exposed end to end.
