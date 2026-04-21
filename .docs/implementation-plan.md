# Flights Search Implementation Plan

## Purpose

This document is the forward-looking roadmap for the greenfield
`flights_search` package. For current repo status, use
`.docs/implementation-progress.md`.

## Scope

The package is being built around two product capabilities only:

1. search Google Flights from a structured request
2. resolve booking URL candidates for an explicitly selected itinerary

The `legacy/` tree can still be used for behavior discovery and fixture
research, but it is not a compatibility target.

## Target Deliverables

- root package at `src/flights_search/`
- stable public typed API
- request and result models
- encoder subsystem for initial, follow-up, and booking flows
- HTTP client subsystem for Google Flights retrieval
- parser subsystem for initial and follow-up results
- booking subsystem for selected-itinerary link resolution
- representative fixtures and automated tests
- focused docs for architecture, plan, and current progress

## Working Sequence

### Phase 1. Finish the runtime search path

Goal:
Turn the existing model and encoder foundation into a working search flow.

Tasks:

- implement the client contract for Google Flights HTML retrieval
- define headers, timeout defaults, retries, and cookie behavior
- add retrieval fixtures or fixture-capture guidance if needed
- implement parser support for initial search results
- wire `search_flights(...)` to encoder + client + parser

Exit criteria:

- a structured one-way search request can produce typed `SearchResults`
- tests cover the initial search flow end to end with fixtures

### Phase 2. Finish round-trip follow-up search

Goal:
Support the two-stage selection flow required for round-trip behavior.

Tasks:

- implement parser support for follow-up payloads
- preserve continuation state in typed results
- support follow-up client retrieval from selected outbound legs
- verify the `encode_follow_up_request(...)` contract against parser inputs

Exit criteria:

- an initial round-trip search can return outbound options
- an outbound selection can drive a follow-up request for return options
- tests cover the follow-up flow with committed fixtures

### Phase 3. Implement booking resolution

Goal:
Resolve booking links for a selected itinerary without coupling booking lookup
to the search API.

Tasks:

- implement `get_booking_urls(...)`
- decide on HTTP-first extraction versus browser-assisted fallback
- keep any browser automation isolated inside `booking/`
- add fixtures and tests for one-way and round-trip booking flows

Exit criteria:

- callers can convert a `FlightSearchRequest` plus `SelectedItinerary` into
  booking URL candidates through the explicit booking API

### Phase 4. Tighten tooling and docs

Goal:
Keep tooling and docs aligned with the active implementation.

Tasks:

- align `pixi` tasks with the available Python executable in managed and local
  environments
- expand README usage examples once runtime search works
- keep `.docs/implementation-progress.md` current as subsystems land
- trim or reorganize docs if implementation creates new ambiguity

Exit criteria:

- developer tasks run consistently
- docs clearly separate architecture, plan, and status

## Constraints

- The public API should not expose raw Google Flights transport fields such as
  `tfs` or `tfu`.
- Search and booking remain separate operations.
- Booking URLs should not be attached to search results by mutation.
- Multi-segment selected legs are part of the base design, not an optional
  extension.
- The greenfield root package is the active implementation surface.

## Deferred Until Needed

- provider abstraction layers
- vendor-specific integrations
- compatibility shims for the legacy package API
- airport-search helpers and generated airport assets
- debug-heavy runtime capture utilities outside the booking subsystem
