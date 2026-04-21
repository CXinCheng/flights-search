# Greenfield Flights Search Build Plan

## Summary

Build a new flights-search package from scratch around one product only:

1. search flights
2. resolve booking URLs for a user-selected itinerary

This is not a refactor. It is a greenfield implementation with a new internal structure, new public API, and new tests. Existing legacy code may be consulted for behavior discovery, but it is not a migration target, a compatibility requirement, or a structural constraint.

The implementation should optimize for a small, explicit architecture with clear subsystem boundaries:

- request models
- transport encoding
- HTTP retrieval
- result parsing
- booking-link resolution

The output of the design phase should be a new architecture/spec document saved as `.docs/core-architecture-redesign.md`. That document should describe the target system we are going to build, not how the legacy package works.

## Product Scope

The new package supports only these runtime capabilities:

- submit a structured Google Flights search request
- parse flight options from the returned Google Flights page
- model user selection of an itinerary
- resolve booking URL candidates for a selected itinerary

The new package does not need to preserve any legacy public API, terminology, file layout, or extension points.

## Architecture Goals

The new build should be organized around five focused subsystems:

- `models`
  - defines request models such as trip leg, passengers, selected segment, selected itinerary, search request, and booking request
  - defines response models such as flight option, flight segment, airport reference, carbon data, and search results
- `encoder`
  - converts normalized request models into Google Flights transport data
  - owns protobuf usage, `tfs` encoding, and follow-up request parameter construction
  - contains no network or parsing logic
- `client`
  - performs direct HTTP requests to Google Flights
  - exposes a narrow API for fetching search HTML and any booking-related page content needed by the booking subsystem
- `parser`
  - parses Google Flights HTML and embedded payloads into typed result models
  - explicitly handles both initial search payloads and follow-up payloads used in selected-itinerary flows
- `booking`
  - resolves booking links for an already selected itinerary
  - owns browser automation if browser automation is still required
  - does not mutate search results as a side effect

## Public API Goals

Expose a minimal top-level API for the new package:

- `FlightSearchRequest`
- `TripLeg`
- `Passengers`
- `SelectedSegment`
- `SelectedItinerary`
- `SearchResults`
- `search_flights(request)`
- `build_booking_request(...)`
- `get_booking_urls(request)`

Optional convenience API:

- `get_booking_url(request)` if returning the first successful link is meaningfully useful

Public API defaults:

- no plain-string query mode
- no filter alias terminology
- no exposed transport fields such as raw `tfs` or `tfu`
- no integration or provider abstraction in the main search API
- no public HTML-fetch helper unless we later decide it is required for debugging or advanced users

## Explicit User Flows

The design document should make the supported flows explicit.

### One-way flow

1. create a structured search request
2. search outbound options
3. choose one option
4. build a selected-itinerary booking request
5. resolve booking URL candidates

### Round-trip flow

1. create a structured round-trip search request
2. search outbound options
3. choose an outbound option
4. perform a follow-up search for return options using the outbound selection
5. choose a return option
6. build a final selected-itinerary booking request
7. resolve booking URL candidates

Important modeling rule:

- transport-specific fields such as `tfu` and selected-flight injection are internal implementation details owned by request builders and the encoder
- the primary public API should speak in terms of search requests, selected segments, and selected itineraries

## Non-Goals

The architecture/spec should explicitly treat the following as out of scope unless later re-approved:

- preserving the legacy module layout
- compatibility shims for old imports or function names
- Bright Data or any other vendor-specific integrations
- generic provider or integration base classes
- airport enum generation and airport search helpers
- debug-oriented browser capture utilities in runtime code
- stale documentation that describes non-existent APIs
- example scripts or tests tied to the legacy surface

## Build Strategy

Because this is a greenfield build, the implementation plan should assume:

- new package modules can be created without matching legacy filenames
- tests should be written for the new API rather than adapted from legacy tests
- legacy code can be mined for request encoding details, parsing behavior, and follow-up flow semantics
- legacy behavior should only be preserved when it supports the new product scope
- anything not required by the new product can be omitted, even if it exists in legacy

The implementation should prefer a sequence like:

1. define typed request and response models
2. implement request encoding for one-way search
3. implement HTML retrieval for direct Google Flights search
4. implement parser support for initial result payloads
5. implement follow-up request encoding for selected outbound flows
6. implement parser support for follow-up payloads
7. implement booking request modeling and booking-link resolution
8. add package-level API exports
9. write or update docs for the new API only

## Design Decisions To Lock In

The architecture document should settle these choices so implementation can proceed without reopening scope repeatedly:

- protobuf-generated files are internal implementation details of the encoder
- request models own language, currency, seat, trip, and passenger settings
- parser output is strongly typed and isolated from raw payload indexing
- search and booking are separate operations with separate APIs
- booking URLs are not attached to search results by mutation
- the primary search return type is `SearchResults`
- booking-link resolution is best-effort and may return an empty list when no links are extractable
- browser automation is allowed only inside the booking subsystem if HTTP-only extraction is insufficient

## Test Plan

The new design should require tests for the greenfield implementation, not migration behavior:

- encode a one-way search request into valid Google Flights params
- fetch and parse an initial search response into typed results
- encode a follow-up round-trip request using an outbound selection
- parse a follow-up response into return-flight options
- build a final selected-itinerary booking request for one-way selection
- build a final selected-itinerary booking request for round-trip selection
- resolve booking URL candidates for a selected one-way itinerary
- resolve booking URL candidates for a selected round-trip itinerary
- confirm search APIs do not implicitly trigger booking resolution
- confirm booking APIs require explicit itinerary selection data
- confirm no legacy aliases or deprecated entry points are part of the new public API

## Assumptions

- this work is a greenfield implementation, not a compatibility-preserving refactor
- the legacy package is reference material only
- direct Google Flights retrieval is the only supported search transport
- local booking-link capture remains the only supported booking-link resolution path unless a better direct approach is discovered during implementation
- the architecture/spec markdown created during implementation should be saved as `.docs/core-architecture-redesign.md`
- the design document should be written as an implementation spec, not user-facing marketing documentation
