# Implementation Progress

## Snapshot

Last reviewed: 2026-04-22

The root `flights_search` package has an implemented typed model layer, a
working request encoder, a retrying HTTP client with cookie persistence,
HTML/payload parser support,
top-level API exports, and test coverage for those pieces.

The runtime booking-resolution subsystem now uses a Playwright-driven
booking-results capture flow because the booking page HTML shell does not
reliably expose booking links by itself.

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
- transient HTTP retry handling and per-client cookie persistence
- HTML and payload parsing in `src/flights_search/parser/`
- `search_flights(...)` wired through encoder + client + parser
- `search_follow_up_flights(...)` wired through follow-up encoder + client +
  parser
- Tests for models, encoder behavior, parser behavior, payload fixture
  documentation, search API wiring, and public API exports

### Present but not implemented

- committed live booking fixtures
- broader validation across more routes and round-trip selections

## Verification

Current test command run on 2026-04-22:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Result:

- 42 tests ran
- all tests passed

## Status By Area

### Public API

Status: implemented first runtime slice

Completed:

- public model exports are in place
- `search_flights(...)` executes the initial search runtime path
- `search_follow_up_flights(...)` executes the round-trip return-options path
- `build_booking_request(...)` returns a typed `BookingRequest`
- `get_booking_urls(...)` executes the booking runtime path
- `get_booking_url(...)` resolves the first candidate at runtime

Remaining:

- validate booking retrieval against stable live responses

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

Status: implemented hardened first slice

Completed:

- shared default headers and timeout defaults
- transient retry handling for retryable status codes and request failures
- per-client cookie persistence across successive retrievals

Remaining:

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

Status: implemented first Playwright-backed slice

Completed:

- live validation that the booking page HTML shell does not expose booking
  links directly
- Playwright capture of `GetBookingResults` payloads from the booking page
- booking-link extraction from direct, structured, and line-framed response
  text
- booking API tests for runtime resolution and empty-result behavior

Remaining:

- validate extraction against more stable live booking responses
- decide whether we need committed sanitized booking payload fixtures in
  addition to unit-level synthetic coverage
- add committed live booking fixtures once stable captures are available

## Recommended Next Steps

1. Validate the client/parser path against real captured HTML fixtures once a
   stable retrieval setup is available.
2. Capture and sanitize representative live booking payload fixtures so the
   Playwright-backed flow has regression coverage against real responses.
