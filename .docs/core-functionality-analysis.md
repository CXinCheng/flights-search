# Core Functionality Analysis

## Goal of the repo

The real working purpose of this repository is narrower than the docs suggest:

1. Build a Google Flights search request.
2. Fetch the Google Flights results page HTML.
3. Parse flight options out of embedded page data.
4. Optionally perform a follow-up flow to obtain a booking URL for a selected itinerary.

Everything else in the repo is either support code for that flow, packaging/docs, or legacy/stale surface area.

## Actual runtime flow

The current runtime path is:

1. `fast_flights/querying.py`
   Creates the encoded Google Flights request payload.
2. `fast_flights/fetcher.py`
   Sends the request to Google Flights or to an integration that returns equivalent HTML.
3. `fast_flights/parser.py`
   Extracts and normalizes result rows from embedded `ds:1` page data.
4. `fast_flights/model.py`
   Defines the parsed result objects returned to callers.
5. `fast_flights/browser_capture.py`
   Optional Playwright-based step used only when we need booking links and no integration provides them.

In package terms, `fast_flights/__init__.py` exposes this public API:

- `FlightQuery`
- `Passengers`
- `SelectedFlight`
- `create_query`
- `get_flights`
- `fetch_flights_html`

## Core modules and what they do

### 1. Query construction

File: `fast_flights/querying.py`

This is one of the most important files in the repo.

Responsibilities:

- Defines `FlightQuery`, which captures a requested segment:
  - date
  - origin airport
  - destination airport
  - optional max stops
  - optional airline filter
- Defines `Passengers`
- Defines `Query`, the full request object
- Serializes query data into protobuf bytes and then base64 for the `tfs` parameter
- Builds both search URLs and booking URLs
- Supports follow-up selected-itinerary flows through:
  - `tfu`
  - `selected_flight`
  - `selected_outbound_flight`
  - `selected_return_flight`

Important detail:

The selected-flight logic is not incidental. It is the mechanism that makes booking URL retrieval possible for:

- one-way selected flight follow-up
- round-trip outbound selection
- round-trip final selected outbound + selected return booking lookup

This file is clearly core.

### 2. Fetching search HTML

File: `fast_flights/fetcher.py`

This is the entry point for live searches.

Responsibilities:

- `fetch_flights_html(...)`
  - uses `primp.Client` by default
  - requests `https://www.google.com/travel/flights`
  - passes either structured query params or a plain text query
- `get_flights(...)`
  - fetches HTML
  - chooses parsing mode based on `Query.tfu`
  - parses the results
  - optionally enriches results with booking URLs
- `_attach_booking_urls(...)`
  - guards follow-up logic so booking URLs are only fetched when enough selection data exists
  - uses an integration override if available
  - otherwise falls back to Playwright capture

This file is core.

### 3. Parsing Google Flights result data

File: `fast_flights/parser.py`

This is the HTML-to-results translator.

Responsibilities:

- Finds the embedded `script.ds:1` block
- Extracts the `data:` payload from Google’s callback script
- Parses metadata:
  - airlines
  - alliances
- Parses result rows into normalized Python dataclasses
- Handles both payload shapes:
  - initial search response via payload index `2`
  - follow-up response via payload index `3`

Produced objects:

- `Flights`
- `SingleFlight`
- `Airport`
- `CarbonEmission`
- attached metadata list via `MetaList`

This file is core.

### 4. Result data model

File: `fast_flights/model.py`

Defines the public shape of parsed results:

- `SingleFlight`
- `Flights`
- supporting dataclasses like `Airport`, `SimpleDatetime`, `CarbonEmission`

This file is core because it is the output contract of the search API.

### 5. Booking link extraction

File: `fast_flights/browser_capture.py`

This file is related to core functionality, but only for the booking-URL half of the product.

Responsibilities:

- opens the booking page with Playwright
- watches for `GetBookingResults` responses
- extracts booking redirect links from response payloads
- supports both:
  - one-shot booking-link fetch
  - debug capture of raw response payloads

Only some functions here are essential for the narrowed target:

- `_extract_booking_links(...)`
- `fetch_booking_links(...)`
- `fetch_booking_links_for_query(...)`

The capture/debug utilities are likely non-core:

- `CapturedBookingResponse`
- `_write_capture(...)`
- `capture_booking_results(...)`
- `capture_booking_results_for_query(...)`
- `keep_browser_open_and_capture(...)`

If the repo is reduced to just “search flights + get booking URL”, this file should probably be trimmed, not removed entirely.

## Support modules that may still be needed

### Protobuf definitions

Files:

- `fast_flights/pb/flights.proto`
- `fast_flights/pb/flights_pb2.py`
- `fast_flights/pb/flights_pb2.pyi`

These are core dependencies of query generation. They should stay unless query serialization is rewritten by hand.

### Types

File: `fast_flights/types.py`

This provides type aliases for:

- `Language`
- `Currency`
- `SeatType`
- `TripType`

This is lightweight and directly tied to the query API, so it is still useful.

### Integration abstraction

Files:

- `fast_flights/integrations/base.py`
- `fast_flights/integrations/__init__.py`
- `fast_flights/integrations/bright_data.py`

These are not the core business logic, but they are adjacent.

Assessment:

- `integrations/base.py`
  - small abstraction
  - still meaningful if we want pluggable fetch/booking backends
- `integrations/bright_data.py`
  - optional vendor-specific transport
  - not required for the minimal product goal
- `integrations/__init__.py`
  - package surface only

If the target is a lean repo focused only on direct flight search and booking URL retrieval, Bright Data support is a strong candidate for removal.

## Files that appear stale, legacy, or non-core

### Stale docs

Files under `docs/` describe APIs that do not match the current package:

- `docs/index.md`
- `docs/filters.md`
- `docs/fallbacks.md`
- `docs/local.md`
- `docs/airports.md`

Examples of drift:

- references to `FlightData` in the public API, while the actual API uses `FlightQuery`
- references to `Result`, `get_flights_from_filter`, `fetch_mode`, and `search_airports`, which are not implemented in the current package
- references to fallback/serverless modes that no longer exist in the codebase

These docs are not reliable descriptions of the current runtime system.

### Stale example / test script

- `test_bright_data.py`

This script appears to target an older API:

- imports `create_filter`
- imports `get_flights_from_filter`
- imports `FlightData`

Those do not match the current runtime interface exposed by `fast_flights/__init__.py`.

This file looks obsolete and is a good removal candidate.

### Generated enum / airport assets

Files:

- `enums/airports.csv`
- `enums/_generated_enum.py`
- `enums/generate_enums.py`
- docs references to airport search helpers

The active package does not currently expose airport-search functionality. The runtime query API accepts airport codes directly as strings.

Unless there is a hidden consumer outside this repo, the airport enum generation path looks non-core.

### Utility scripts

Files:

- `scripts/extract_langs.py`
- `scripts/extract_currencies.py`

These appear to be one-off generation/helpers for maintaining literals in `types.py`.
They are not part of the runtime flight-search flow.

### Packaging/docs infra

Files:

- `mkdocs.yml`
- `setup.py`
- possibly parts of `README.md`

These are not runtime code, though they may still matter for publishing.

## Test coverage observations

File: `tests/test_round_trip_token_flow.py`

This is the most useful test file for understanding the true product behavior. It validates:

- query encoding
- one-way selected-flight follow-up
- round-trip `tfu` flow
- final booking URL enrichment behavior
- parser behavior for both payload shapes

This test file captures the current real product better than the docs do.

Important mismatch found:

- the test imports `_extract_first_booking_link` from `fast_flights.browser_capture`
- that function does not exist in the current implementation

That suggests the tests are partially stale or the implementation is partially incomplete. This should be resolved during refactor so the remaining code and tests describe the same public behavior.

## What is actually “core functionality”

For the requested simplification, the irreducible core looks like this:

1. Input model for a flight search
2. Query encoding to Google Flights `tfs`
3. Search request execution
4. HTML/script payload parsing into normalized results
5. Follow-up selected-itinerary logic to obtain booking URLs

Translated to files, the likely keep-set is:

- `fast_flights/__init__.py`
- `fast_flights/querying.py`
- `fast_flights/fetcher.py`
- `fast_flights/parser.py`
- `fast_flights/model.py`
- `fast_flights/types.py`
- `fast_flights/pb/*`
- maybe a reduced `fast_flights/browser_capture.py`

Potential keep-if-needed:

- `fast_flights/integrations/base.py`

Strong removal candidates for a “minimal core only” refactor:

- `fast_flights/integrations/bright_data.py`
- possibly the entire `fast_flights/integrations/` package if third-party integrations are out of scope
- `scripts/*`
- `enums/*`
- `test_bright_data.py`
- most or all current `docs/*` pages, to be replaced with a smaller accurate spec
- debug-oriented capture helpers inside `browser_capture.py`

## Refactor direction recommendation

If we proceed with a full repo simplification, the clean target architecture should probably be:

- `query.py`
  request building and selected-itinerary encoding
- `client.py`
  direct Google Flights fetch
- `parser.py`
  HTML and payload parsing
- `booking.py`
  booking link extraction only
- `models.py`
  request/result dataclasses

Even if filenames do not change, the conceptual boundaries above are the right minimal product boundaries.

## Bottom line

The codebase already contains a workable core for:

- searching flights
- selecting a specific itinerary
- obtaining a booking URL

The biggest cleanup opportunity is not hidden business logic. It is removing drift:

- stale docs
- stale examples
- stale tests/scripts
- optional vendor integrations
- unused airport enum generation assets
- debug capture utilities that exceed the narrowed product goal

That means the upcoming refactor can be aggressive without losing the essential functionality, as long as we preserve:

- query encoding
- fetching
- parsing
- selected-itinerary follow-up flow
- booking link extraction
