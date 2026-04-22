# Flights Search MCP Server Implementation Progress

## Snapshot

Last reviewed: 2026-04-22

The MCP server is no longer at planning-only stage. Phase 1, Phase 2, Phase 3,
and Phase 4 are complete.

Current status:

- same-repo MCP approach remains the active implementation path
- `src/flights_search_mcp/` now exists with server bootstrap, tool
  registration, schemas, adapters, and error helpers
- the project now depends on the `mcp` Python package and exposes the
  `flights-search-mcp` console entry point
- the server currently exposes `server_info`, `search_flights`,
  `search_return_flights`, and `resolve_booking_urls`
- booking resolution is now exposed through the MCP layer with explicit
  itinerary validation ahead of the domain booking helpers
- MCP-layer unit coverage exists for server registration, request/response
  adaptation, outbound selection handle encoding/decoding, and validation
  failure behavior
- README now includes local `stdio` launch instructions plus MCP tool-contract,
  success-payload, and failure-payload examples
- the planned Phase 2 live derivation probe and real `stdio` MCP validation
  were completed and recorded on 2026-04-22
- the planned Phase 3 real `stdio` MCP follow-up validation was completed and
  recorded on 2026-04-22
- the planned Phase 4 real `stdio` MCP booking validation was completed and
  recorded on 2026-04-22

## Current Repo Status

### Completed

- created `.docs/mcp-server/implementation-plan.md`
- kept the MCP server implementation in the same repository as
  `flights-search`
- added the MCP package scaffold under `src/flights_search_mcp/`
- selected the `mcp` Python library and added it to `pyproject.toml`
- added `python -m flights_search_mcp.server` and `flights-search-mcp` as the
  canonical local launch paths
- implemented `stdio` server bootstrap in `src/flights_search_mcp/server.py`
- registered the initial tool set in `src/flights_search_mcp/tools.py`
- implemented `server_info`
- implemented the initial `search_flights` MCP tool over
  `flights_search.search_flights(...)`
- added MCP-facing schemas, adapters, and structured error helpers
- implemented outbound selection handle encoding for round-trip search results
- implemented MCP-layer tests in:
  - `tests/test_mcp_server.py`
  - `tests/test_mcp_schemas.py`
- documented local MCP setup, launch commands, tool-contract notes, and
  example MCP payloads in `README.md`

### Partially Implemented

- MCP runtime verification:
  Phase 2 scope is now recorded with a live `search_flights` validation over
  `stdio`, but broader live validation across more routes still remains future
  hardening work

### Not Yet Implemented

- explicit integration notes for the downstream MCP consumer
- broader live validation coverage across more real route shapes

## Status By Area

### Repository Decision

Status: complete for now

Completed:

- chose same-repo implementation for the initial MCP version
- recorded the reasons and tradeoffs in the implementation plan

Remaining:

- revisit repo split only if the MCP contract stabilizes and multiple consumers
  appear

### Tool Contract

Status: in progress

Completed:

- identified the minimal tool surface for the first version
- kept the MCP boundary stateless
- implemented concrete schemas for the currently exposed search tool boundary
- implemented structured `search_flights` outputs with machine-oriented segment
  fields
- implemented `selected_leg` output for selectable results
- implemented opaque outbound selection handle encoding for round-trip initial
  search results
- implemented explicit non-selectable marking through
  `selection_unavailable_reason`
- documented and implemented request-leg date derivation for selection payloads
- implemented structured MCP tool-failure payloads for validation and mapped
  runtime failures
- completed the planned Phase 2 live derivation probe on 2026-04-22 for
  `SFO -> LAX` on `2026-05-20` and `SFO -> LAX -> SFO` on
  `2026-05-20 / 2026-05-27`
- completed a real `stdio` MCP client validation on 2026-04-22 using
  `search_flights`

Remaining:

- verify the current field set against downstream agent needs in a real client
  flow
- confirm with live sampling whether any production result classes need
  additional `selection_unavailable_reason` handling
- decide whether the MCP boundary should explicitly reject `trip_type="multi-city"`
  up front until a corresponding tool contract exists

### Server Runtime

Status: Phase 1 complete

Completed:

- selected `stdio` as the first transport
- chose `mcp.server.fastmcp.FastMCP` for bootstrap
- added the runtime dependency in `pyproject.toml`
- implemented server bootstrap in `src/flights_search_mcp/server.py`
- registered the initial tool set
- documented canonical launch commands in `README.md`

Remaining:

- no additional Phase 1 work; future runtime work is tied to new tools and
  broader live validation

### Adapters And Errors

Status: in progress

Completed:

- added explicit MCP-facing schema models in `src/flights_search_mcp/schemas.py`
- implemented request adaptation from MCP payloads into
  `FlightSearchRequest`
- implemented domain search result adaptation into structured MCP responses
- implemented outbound selection handle encode/decode helpers
- implemented follow-up handle validation against the original first search leg
- implemented follow-up result adaptation into `selected_itinerary` payloads
- implemented booking-itinerary validation and booking URL response adaptation
- implemented stable error payload helpers in
  `src/flights_search_mcp/errors.py`
- mapped validation, HTTP/network, parser/value, and Playwright runtime failure
  classes into structured MCP tool errors
- mapped unsupported non-round-trip follow-up usage to
  `error.code = "unsupported_usage"`

Remaining:

- add tests for unsupported-usage branches once follow-up and booking tools
  exist

### Search Integration

Status: Phase 2 and Phase 3 complete

Completed:

- implemented the initial `search_flights` MCP tool
- wired the tool to `flights_search.search_flights(...)`
- covered the happy path with MCP server tests
- covered validation failure behavior with MCP server tests
- covered selection-payload date derivation with adapter tests
- covered non-selectable option handling when segment identity is incomplete
- covered outbound selection handle decoding validation for malformed payloads
- implemented the `search_return_flights` MCP tool
- wired it to `flights_search.search_follow_up_flights(...)`
- added round-trip-only handle validation for follow-up requests
- added `selected_itinerary` outputs for follow-up options
- covered follow-up request forwarding and response shaping with MCP tests
- mapped non-round-trip follow-up requests to `unsupported_usage`

Remaining:

- broaden live validation coverage beyond the current closeout samples

### Booking Integration

Status: complete

Completed:

- confirmed that the current domain package already exposes booking request
  construction and URL resolution helpers
- carried the existing Playwright Chromium runtime prerequisite into MCP error
  planning and README guidance
- implemented the `resolve_booking_urls` MCP tool
- added explicit itinerary-to-request invariant checks before calling the
  domain booking helpers
- fixed the MCP booking path to run Playwright-backed booking resolution off
  the asyncio event loop
- added MCP tests for booking request forwarding, itinerary mismatch
  validation, missing Playwright runtime error mapping, and missing browser
  runtime error mapping
- completed a real `stdio` MCP booking validation on 2026-04-22 with:
  `python ..\scripts\live_test.py mcp-phase4-closeout --date 2026-05-20 --origin SFO --destination LAX`

Remaining:

- broaden booking-path live validation beyond the current closeout sample

### Testing

Status: in progress

Completed:

- added MCP-layer unit tests for server bootstrap and tool registration
- added MCP-layer unit tests for request adaptation defaults and validation
- added MCP-layer unit tests for structured search result adaptation
- added MCP-layer unit tests for selection-handle round-tripping and malformed
  payload rejection
- added MCP-layer unit tests for follow-up handle validation and follow-up tool
  request forwarding
- added MCP-layer tests for unsupported follow-up usage classification
- added MCP-layer tests for booking request forwarding, itinerary validation,
  and booking runtime error mapping for missing Playwright and browser runtime
  prerequisites
- re-ran the current MCP tests successfully on 2026-04-22 with:
  `PYTHONPATH=src python -m unittest tests.test_mcp_server tests.test_mcp_schemas`
- completed a real `stdio` MCP follow-up validation on 2026-04-22 with:
  `python ..\scripts\live_test.py mcp-phase3-closeout --outbound-date 2026-05-20 --return-date 2026-05-27 --origin SFO --destination LAX`
- completed a real `stdio` MCP booking validation on 2026-04-22 with:
  `python ..\scripts\live_test.py mcp-phase4-closeout --date 2026-05-20 --origin SFO --destination LAX`

Remaining:

- add targeted tests for unsupported-usage branches
- broaden live validation coverage beyond the current closeout sample routes

### Documentation

Status: in progress

Completed:

- MCP implementation plan created
- this progress document updated to reflect actual code status
- README now includes an MCP server section with launch commands and setup flow
- README now includes MCP tool-contract notes for opaque handles, request-leg
  date derivation, and MCP tool-failure behavior
- README now includes concrete request and success payload examples for
  `search_flights`, `search_return_flights`, and `resolve_booking_urls`
- README now includes example structured failure payloads for validation and
  booking-runtime prerequisites
- README now includes the Phase 2, Phase 3, and Phase 4 closeout validation
  commands
- README now records the current sample live-validation results for both the
  initial search flow and the round-trip follow-up flow

Remaining:

- add integration notes for the consuming project
- broaden MCP docs only if downstream integration reveals contract gaps

## Phase Status

### Phase 1: Skeleton

Status: complete

Delivered:

- package scaffold under `src/flights_search_mcp/`
- MCP dependency selection and `pyproject.toml` update
- `stdio` bootstrap
- initial tool registration
- canonical local launch commands in README and console scripts

Exit criteria check:

- the server starts successfully:
  satisfied by implemented bootstrap and passing server tests
- the tool list is visible to an MCP client:
  satisfied in-process by `test_server_lists_registered_tools`
- the canonical local launch command is documented and exercised once:
  documented in README; explicit client-side exercise note is still thin, but
  Phase 1 implementation itself is complete

### Phase 2: Search tool

Status: complete

Delivered:

- `search_flights` schema
- request and response adapters
- tool handler wired to `flights_search.search_flights(...)`
- unit tests for happy path and validation errors
- selection-payload derivation logic for request-leg dates
- non-selectable option handling and outbound selection handle encoding
- explicit live derivation probe recorded on 2026-04-22
- real MCP-client validation pass over `stdio` recorded on 2026-04-22

Closeout evidence:

- live one-way derivation probe:
  `SFO -> LAX` on `2026-05-20` returned 4 options; all 4 were selectable and
  none required `selection_unavailable_reason`
- live round-trip initial derivation probe:
  `SFO -> LAX -> SFO` on `2026-05-20 / 2026-05-27` returned 3 options; all 3
  were selectable and all 3 emitted `outbound_selection_handle`
- live `stdio` MCP client validation:
  the client initialized the server, listed `server_info` and
  `search_flights`, then executed `search_flights` successfully for
  `SFO -> LAX` on `2026-05-20` with `selection_phase="initial"` and 4 returned
  options

### Phase 3: Follow-up tool

Status: complete

Delivered:

- `search_return_flights` schema exposure through the MCP tool boundary
- outbound-selection-handle decoding and first-leg validation
- tool handler wired to `flights_search.search_follow_up_flights(...)`
- follow-up response adaptation with `selected_itinerary` outputs
- unit tests for handle decoding, continuation validation, and selected-outbound
  request validation

Exit criteria check:

- an MCP client can execute the round-trip follow-up flow using returned
  outbound selection handles:
  satisfied by a real `stdio` MCP client validation on 2026-04-22 using
  `python ..\scripts\live_test.py mcp-phase3-closeout --outbound-date 2026-05-20 --return-date 2026-05-27 --origin SFO --destination LAX`

### Phase 4: Booking tool

Status: complete

Delivered:

- `resolve_booking_urls` schema exposure through the MCP tool boundary
- itinerary validation adapters for explicit booking selections
- tool handler wiring to booking request construction and booking URL
  resolution
- a fix for the live MCP booking path so Playwright-backed booking resolution
  runs outside the asyncio event loop
- tests for booking request forwarding, itinerary mismatch validation, missing
  Playwright runtime messaging, and missing browser runtime messaging

Closeout evidence:

- real `stdio` MCP client booking validation on 2026-04-22:
  `python ..\scripts\live_test.py mcp-phase4-closeout --date 2026-05-20 --origin SFO --destination LAX`
- recorded result:
  the client listed `server_info`, `search_flights`, `search_return_flights`,
  and `resolve_booking_urls`, then executed a one-way search plus booking flow
  successfully with `selection_phase="initial"`, 4 returned options, a
  populated `selected_leg`, and 2 booking URLs

## Immediate Next Steps

1. Add downstream integration notes for the consuming project.
2. Broaden live validation beyond the current Phase 2/3/4 closeout samples.
3. Decide whether any additional MCP doc examples are needed after first
   downstream integration.

## Verification

Current verification status:

- MCP package scaffold exists and is wired into the project package metadata
- server bootstrap and tool registration are covered by unit tests
- `search_flights` request forwarding and structured response shaping are
  covered by unit tests
- selection-handle encoding/decoding and non-selectable option behavior are
  covered by unit tests
- current MCP tests passed locally on 2026-04-22
- booking request forwarding, itinerary validation, and booking runtime error
  mapping are now covered by MCP tests
- live derivation probe completed on 2026-04-22 and recorded in the repo docs
- full `stdio` MCP client validation completed on 2026-04-22 and recorded in
  the repo docs
- real `stdio` MCP client validation for the Phase 3 follow-up flow completed
  on 2026-04-22 and is now recorded in the repo docs
- real `stdio` MCP client validation for the Phase 4 booking flow completed on
  2026-04-22 and is now recorded in the repo docs

## Completion Signal

This tracker should report the MCP server as broadly implemented once the repo
contains:

- the current runnable `stdio` MCP server with the planned search, follow-up,
  and booking tools
- MCP-layer tests for all exposed tools
- recorded live validation through a real MCP client path
- enough documentation for the consuming project to use the server without
  reading the internals of `flights_search`
