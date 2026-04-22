# Flights Search MCP Server Implementation Plan

## Purpose

This document defines the implementation plan for exposing the existing
`flights_search` package as an MCP server within the same repository. The goal
is to make the current search and booking capabilities available to another AI
agent through a stable tool contract without turning the MCP layer into a
second business-logic implementation.

The MCP server should remain a thin protocol adapter over the existing typed
package surface in `src/flights_search/`.

## Decision

The MCP server will live in the same repository as `flights-search` for the
initial implementation.

Reasons:

- the domain API is still close enough to the implementation that co-evolving
  the package and the MCP layer is lower risk than splitting repos now
- local iteration will be faster while the tool contract is still being shaped
- the current package already has the right public entry points for a thin MCP
  adapter

This decision does not prevent extracting the MCP layer into a separate
repository later if the contract stabilizes and multiple consumers emerge.

## Goals

1. Expose the current supported runtime capabilities as MCP tools.
2. Keep the server stateless at the protocol boundary wherever practical.
3. Reuse the current typed package API instead of duplicating request-building,
   parsing, or booking logic.
4. Return agent-friendly structured results rather than leaking raw Google
   Flights transport details.
5. Make operational failures actionable, especially network errors and missing
   Playwright runtime prerequisites.

## Non-Goals

- redesigning the core `flights_search` package around MCP concerns
- exposing raw transport fields such as `tfs` or `tfu`
- persisting server-side sessions, search caches, or user state in the first
  implementation
- adding new flight-search product features just because the MCP layer exists
- building a multi-tenant hosted service in the first implementation

## Current Reusable Surface

The MCP layer should treat the existing package as the domain boundary and
adapt only the public API:

- `search_flights(request)`
- `search_follow_up_flights(request, continuation, selected_outbound_leg)`
- `build_booking_request(request, itinerary)`
- `get_booking_urls(request)`
- `get_booking_url(request)`

The relevant public models already exist under `src/flights_search/models/`
and are sufficient to drive most of the schema design. The MCP adapter still
needs explicit boundary rules for fields that are not carried through the
current parsed result objects verbatim.

## Proposed Package Shape

The MCP implementation should be added as a sibling package under `src/`.

```text
src/
  flights_search/
  flights_search_mcp/
    __init__.py
    server.py
    tools.py
    schemas.py
    adapters.py
    errors.py
tests/
  test_mcp_server.py
  test_mcp_schemas.py
```

Suggested responsibilities:

- `server.py`: MCP server bootstrap and tool registration
- `tools.py`: tool handlers and MCP-facing orchestration
- `schemas.py`: MCP input and output schema definitions
- `adapters.py`: conversion between MCP payloads and internal dataclasses
- `errors.py`: domain and runtime error normalization for tool responses

## Transport Recommendation

The first implementation should support `stdio` transport.

Reasons:

- it matches the most common local AI-agent integration path
- it avoids introducing HTTP deployment concerns while the tool contract is
  still evolving
- it is sufficient for one local consumer project

HTTP transport can be added later only if a real deployment need appears.

## Tool Surface

The first MCP version should expose only the minimal stable operations.

### 1. `search_flights`

Purpose:
Execute an initial Google Flights search from a structured request.

Inputs:

- trip type
- one or more legs
- passengers
- seat
- language
- currency

Outputs:

- selection phase
- list of returned options
- per-option continuation token when present
- segment-level structured flight data
- per-option selection payload that can be sent back to later MCP tools without
  reconstructing it from display fields

Notes:

- output should include only agent-useful fields
- raw HTML and parser internals should not be returned
- each returned option should include a machine-oriented selection structure for
  downstream follow-up and booking calls

### 2. `search_return_flights`

Purpose:
Execute the round-trip follow-up request after an outbound option is selected.

Inputs:

- original search request
- outbound selection handle

Required handle rule:

- the MCP server should treat the outbound selection handle as an opaque,
  single-option follow-up input produced by `search_flights`
- the handle must carry the continuation token plus the exact selected outbound
  leg payload for the same option
- the caller should not construct this handle manually or mix fields across
  multiple returned options
- the MCP adapter should decode the handle into the current package inputs for
  `search_follow_up_flights(...)`

Required validation rules:

- this tool is supported only for `trip_type == "round-trip"`
- the original search request must contain exactly two legs
- the outbound selection handle must be non-empty and structurally valid
- the decoded `continuation_token` must be non-empty
- the decoded `selected_outbound_leg` must represent the first leg of the
  original search request
- every decoded selected outbound segment must carry the full typed identity
  required by `SelectedSegment`
- if the outbound selection handle cannot be decoded into one coherent option
  selection, the server should reject the request as a validation error rather
  than attempting a best-effort follow-up request

Outputs:

- follow-up selection phase
- returned follow-up options
- segment-level structured flight data

Notes:

- the MCP-facing name should be easier for an agent to understand than the
  internal method name `search_follow_up_flights`
- the implementation should still call the current package API
- this handle-based contract avoids a stateless v1 footgun where a caller could
  otherwise combine a continuation token from one option with a selected leg
  from another option

### 3. `resolve_booking_urls`

Purpose:
Resolve booking URL candidates for an explicit selected itinerary.

Inputs:

- original search request
- selected itinerary

Required validation rules:

- the selected itinerary leg count must match the original search request leg
  count
- for each leg, the first selected segment origin must match the search leg
  origin
- for each leg, the first selected segment date must match the search leg date
- for each leg, the last selected segment destination must match the search leg
  destination
- the MCP adapter should validate these invariants before calling
  `build_booking_request(...)`

Outputs:

- zero or more booking URL candidates

Notes:

- this tool should call `build_booking_request(...)` and `get_booking_urls(...)`
- runtime failures caused by missing Playwright dependencies should be reported
  with explicit remediation guidance

### Optional 4. `server_info`

Purpose:
Return server metadata and basic capability information for debugging.

This is optional but useful when another project is integrating the server for
the first time.

## Schema Design Principles

The MCP schema should be stable and explicit rather than mirroring internal
Python object shapes by accident.

Rules:

- use plain JSON-compatible values at the tool boundary
- represent `ContinuationHandle` as an opaque string token
- keep airport, segment, leg, and itinerary structures explicit
- include machine-friendly fields first; avoid presentation-only prose
- keep naming consistent across tools
- separate display-oriented fields from round-trip-safe selection payloads
- do not require the caller to infer follow-up or booking inputs from
  human-readable text

Recommended output fields for each option:

- `kind`
- `price`
- `airlines`
- `outbound_selection_handle`
- `segments`
- `selected_leg`
- optional aggregate helpers such as `segment_count` and `stop_count`

Recommended output fields for each segment:

- `origin_airport`
- `destination_airport`
- `date`
- `departure_time`
- `arrival_time`
- `duration_minutes`
- `marketing_airline_code`
- `flight_number`
- `aircraft_type`

Required round-trip-safe selection fields:

- every selectable option returned by `search_flights` should include a
  `selected_leg` object for inspection plus an `outbound_selection_handle`
  shaped so it can be passed directly into `search_return_flights`
- every selectable option returned by `search_return_flights` should include a
  `selected_itinerary` object shaped so it can be passed directly into
  `resolve_booking_urls`
- the outbound selection handle should be treated as opaque by consumers even if
  its first implementation is a JSON-serializable encoded structure
- the selection payload should preserve exactly the fields required by the
  current typed models: `origin_airport`, `date`, `destination_airport`,
  `marketing_airline_code`, and `flight_number`
- if the underlying parsed result lacks fields required to build a valid
  selection payload, the adapter should not emit a partially valid structure

Required date-derivation rule for selection payloads:

- the current parsed `FlightSegment` result shape does not include an explicit
  segment date field, while `SelectedSegment` requires `date`
- for the first MCP version, the adapter should derive every
  `selected_leg.segments[*].date` and `selected_itinerary.legs[*].segments[*].date`
  from the corresponding requested search leg date, not from display text
- this rule must be documented as an MCP contract constraint so the adapter
  does not infer dates from prose or locale-sensitive strings
- if future live validation shows that a single search leg can produce
  selectable segments whose required booking identity cannot be represented by
  the request-leg date, the domain package should be extended before widening
  the MCP contract

Required handling for incomplete segment identity data:

- if an option cannot produce a valid selection payload, the MCP layer should
  mark that option as non-selectable
- non-selectable options should include an explicit machine-readable reason such
  as `selection_unavailable_reason`
- the MCP layer should never force the client to guess missing selection fields
  from prose or display formatting

The schema should not require the downstream agent to understand internal
dataclass names or package layout.

## Statelessness Strategy

The first MCP server should be stateless across tool calls.

That means:

- `search_flights` returns any follow-up state needed for later calls inside the
  opaque `outbound_selection_handle`
- `search_return_flights` requires the caller to resend the original search
  request plus the exact `outbound_selection_handle` returned from one option
- `resolve_booking_urls` requires the caller to send the original search
  request plus the explicit selected itinerary

This avoids hidden server memory, simplifies retries, and makes the server safe
to invoke from multiple independent agents or processes.

## Error Handling Plan

The MCP layer should normalize errors into a small set of actionable failure
shapes.

Expected categories:

- input validation error
- upstream request failure
- upstream response parsing failure
- missing Playwright package or browser runtime
- unsupported usage shape

Requirements:

- do not leak raw stack traces in normal tool responses
- preserve enough detail for debugging
- return concrete next steps where the operator can act
- distinguish user-fixable input problems from environment failures

The MCP layer should use one stable error payload shape when reporting tool
failures, but it should not hide operational failures inside a successful tool
result.

At the MCP boundary:

- success responses should return a normal result payload
- input validation, unsupported usage, upstream request failures, upstream
  response failures, and Playwright environment failures should be surfaced as
  tool-level failures using the chosen MCP library's normal error path
- the structured error payload should still use one stable shape so consuming
  agents can parse failure details deterministically
- unexpected implementation bugs may still raise MCP protocol errors and should
  be logged separately from the stable tool contract

Required error fields:

- `code`
- `message`
- `retryable`
- `details`
- `remediation`

Required failure-shape mapping:

- input validation problems should fail the tool with
  `error.code = "validation_error"`
- unsupported but well-formed usage should fail the tool with
  `error.code = "unsupported_usage"`
- upstream request, parsing, and Playwright environment failures should fail
  the tool with the corresponding stable error code
- successful tool results may still contain empty business data, such as zero
  returned booking URLs, but that should not be represented as an execution
  failure

Suggested code set:

- `validation_error`
- `upstream_request_failed`
- `upstream_response_invalid`
- `playwright_missing`
- `browser_runtime_missing`
- `unsupported_usage`

Error mapping should be documented so consuming agents can make deterministic
retry and user-guidance decisions.

The booking flow must explicitly surface the Chromium installation requirement
if Playwright is present but the browser binary is not installed.

## Dependencies And Runtime

The MCP layer should add only the minimum server dependency required to expose
tools. It should continue to rely on the existing package dependencies for
network retrieval and booking capture.

Before implementation:

- choose the MCP Python library to use for server bootstrap
- add it to `pyproject.toml`
- verify that the chosen library supports straightforward `stdio` serving on
  Python 3.11
- define the canonical local launch entry point, for example
  `python -m flights_search_mcp.server` or an equivalent console script
- document the exact command line that the consuming project should execute

The booking tool remains subject to the existing runtime prerequisite:

- `python -m playwright install chromium`

This requirement should be documented in both the README and MCP-specific docs.

The local run documentation should also state the expected installation flow for
the consuming project:

- install project dependencies
- install the Playwright Chromium runtime only if booking resolution is needed
- launch the server through the canonical `stdio` entry point

## Testing Plan

The MCP layer needs its own tests even though the underlying domain package is
already covered.

### Unit coverage

Add tests for:

- schema validation and normalization
- adapter conversion between JSON payloads and internal dataclasses
- tool handler wiring into the domain API
- error mapping for validation, network, and Playwright failures
- selection-payload derivation rules, especially the request-leg date mapping
- unsupported usage validation for non-round-trip follow-up requests and
  itinerary/search-request mismatches

### Behavioral coverage

Use mocks around the domain API to verify:

- `search_flights` forwards the expected request shape
- `search_return_flights` forwards continuation plus selected-leg data
- `resolve_booking_urls` builds the booking request and returns URLs

### Live validation

After unit coverage is in place, run a minimum live MCP validation matrix:

- one-way search through the MCP tool
- round-trip initial search plus follow-up tool call
- booking URL resolution through the MCP tool
- one end-to-end validation through the actual consuming MCP client over
  `stdio`, not only direct in-process tests

The live MCP validation should confirm that protocol serialization has not
damaged the existing domain behavior.

## Documentation Plan

Add MCP-specific documentation in phases.

Required docs:

- this implementation plan
- a short MCP README or section describing how to run the server locally
- example tool payloads for each supported tool
- integration notes for the other project that will consume the server
- the canonical local launch command and required environment prerequisites
- example success and error payloads for each supported tool

Documentation should make clear that:

- `flights_search` remains the domain implementation
- `flights_search_mcp` is a thin adapter
- the initial server is intended for local or controlled agent usage
- selection payload dates are derived from the corresponding request leg date in
  MCP v1
- handled tool failures use a stable structured error payload over the MCP
  tool-failure path, not a success envelope with `ok: false`
- `search_return_flights` consumes an opaque `outbound_selection_handle` rather
  than independently supplied continuation and selection fields

## Implementation Phases

### Phase 1: Skeleton

Deliver:

- package scaffold under `src/flights_search_mcp/`
- MCP library dependency selection
- `stdio` bootstrap
- placeholder tool registration

Exit criteria:

- the server starts successfully
- the tool list is visible to an MCP client
- the canonical local launch command is documented and exercised once

### Phase 2: Search tool

Deliver:

- `search_flights` schema
- request and response adapters
- tool handler wired to `flights_search.search_flights(...)`
- an explicit selection-payload derivation probe over a small live sample to
  confirm which returned options are selectable in MCP v1
- unit tests for happy path and validation errors

Exit criteria:

- an MCP client can execute an initial search and receive structured options
- the repo records whether any sampled live options require
  `selection_unavailable_reason` because required identity fields are missing

### Phase 3: Follow-up tool

Deliver:

- `search_return_flights` schema
- outbound-selection-handle adapter plus decoded selected-leg adapter
- tool handler wired to `search_follow_up_flights(...)`
- tests for handle decoding, continuation validation, and selected-outbound
  validation

Exit criteria:

- an MCP client can execute the round-trip follow-up flow using returned
  outbound selection handles

### Phase 4: Booking tool

Deliver:

- `resolve_booking_urls` schema
- itinerary adapters
- tool handler wired to booking request construction and URL resolution
- tests for missing Playwright runtime messaging

Exit criteria:

- an MCP client can resolve booking URLs from an explicit selected itinerary

### Phase 5: Hardening

Deliver:

- error normalization pass
- MCP-focused README updates
- live validation notes
- any minimum integration examples needed by the consuming project

Exit criteria:

- another local project can launch and use the server without reading the
  internals of `flights_search`

## Risks

### 1. Contract drift

Risk:
The MCP schema may accidentally track internal dataclass changes too closely.

Mitigation:

- define explicit adapter-layer schemas
- test only the MCP contract at the tool boundary
- keep the follow-up handle opaque so internal follow-up inputs can change
  without forcing a client-side schema rewrite

### 2. Hidden state pressure

Risk:
It may be tempting to store previous search results server-side for convenience.

Mitigation:

- keep follow-up state explicit in returned handles rather than process memory
- reject designs that depend on process-local memory as part of the core API

### 3. Selection identity gaps

Risk:
Some live search results may omit fields required to build a valid
`SelectedSegment`, even though the option is displayable to a user.

Mitigation:

- validate selectable identity fields before emitting selection payloads
- mark non-selectable options explicitly with `selection_unavailable_reason`
- run live derivation sampling before freezing the first search-tool contract

### 4. Booking environment fragility

Risk:
Booking resolution depends on Playwright and an installed Chromium runtime.

Mitigation:

- preserve the booking flow as a separate tool
- return explicit remediation messages
- document runtime prerequisites clearly

### 5. Tool overexpansion

Risk:
The MCP server may become a place to add product features unrelated to the
current package scope.

Mitigation:

- keep the first version limited to search, follow-up, and booking resolution
- treat additional tools as separate scope decisions

## Completion Signal

This plan is complete when the repository contains a local `stdio` MCP server
that exposes the minimal supported tool surface, is covered by MCP-layer tests,
and can be consumed by the other project without requiring direct imports from
`flights_search`.
