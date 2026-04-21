# Flights Search Implementation Plan

## Purpose

This document translates the high-level build direction in [.docs/PLAN.md](/Users/xincheng_cai/Documents/CXC/flights-search/.docs/PLAN.md) into an execution plan for a greenfield Python package focused on two product capabilities:

1. Search Google Flights with a structured request.
2. Resolve booking URL candidates for a user-selected itinerary.

The plan assumes the legacy package under `legacy/` is reference material only. We may reuse ideas and verify behavior against it, but we are not preserving its public API, structure, or compatibility surface.

## Working Assumptions

- The new package will be implemented as a fresh Python package at the repository root.
- `pixi` will be the primary tool for environment management, dependency management, and common developer tasks.
- The new package should expose a small typed public API and keep transport details internal.
- Direct Google Flights retrieval is the only supported search transport in the first build.
- Booking URL extraction may use browser automation, but only inside the booking subsystem.

## Target Deliverables

The implementation should produce the following concrete outputs:

- `.docs/core-architecture-redesign.md`
- a new root package for the greenfield implementation
- root-level project metadata configured for `pixi`
- fixture capture guidance and committed representative fixtures for search and follow-up parsing
- typed request and response models
- encoder, client, parser, and booking subsystems
- package-level public API exports
- automated tests for search, follow-up flows, and booking resolution
- focused documentation for the new API only

## Repo And Tooling Plan

### 1. Establish the new repo root as the active package

Create fresh project metadata at the repository root instead of extending `legacy/pyproject.toml`.

Recommended structure:

```text
.
├── .docs/
├── src/
│   └── flights_search/
├── tests/
├── pyproject.toml
├── pixi.lock
└── README.md
```

Recommended package name:

- distribution name: `flights-search`
- import package: `flights_search`

This avoids collisions with the legacy `fast_flights` module and makes the new build clearly separate.

### 2. Use `pixi` as the source of truth for environments

`pixi` should control:

- Python version
- core runtime dependencies
- optional local/browser dependencies
- dev tooling
- repeatable tasks such as test, lint, type-check, and docs checks

Recommended `pyproject.toml` approach:

- keep standard Python package metadata in `[project]`
- use `[tool.pixi.workspace]`, `[tool.pixi.environments]`, and `[tool.pixi.tasks]`
- install the local package in editable mode via `[tool.pixi.pypi-dependencies]`

Recommended environments:

- `default`: runtime package + core dependencies
- `dev`: adds test, lint, and typing tools
- `local`: adds browser automation dependencies for booking-link work

Recommended first-pass tasks:

- `pixi run test`
- `pixi run test-unit`
- `pixi run lint`
- `pixi run typecheck`
- `pixi run format`
- `pixi run docs-check`

Recommended dependency split:

- runtime: `protobuf`, `selectolax`, HTTP client dependency chosen during architecture phase
- local feature: `playwright`
- dev: `pytest`, `pytest-asyncio` if needed, `ruff`, `pyright` or `basedpyright`

### 3. Keep the legacy package isolated

The `legacy/` directory should remain available for reference and fixture extraction, but it should not define the new package layout or tooling workflow.

Implementation rule:

- all new commands, tests, and documentation should target the root package, not `legacy/`

## Architecture Work Breakdown

### Phase 0. Write the architecture spec

Goal:

- produce `.docs/core-architecture-redesign.md` before implementation deepens

This document should lock in:

- root package layout
- model boundaries
- search vs booking API separation
- one-way vs round-trip selection flow
- continuation-token handoff for round-trip follow-up without exposing raw transport fields
- the shape of a selected leg, including support for multiple selected segments within a leg
- encoder responsibilities
- parser responsibilities
- client contract
- booking subsystem contract
- error model and expected best-effort behavior
- fixture sourcing and sanitization rules for parser and booking tests

Exit criteria:

- implementation can proceed without reopening naming, package boundaries, or transport exposure questions

### Phase 1. Bootstrap the new package and tooling

Goal:

- create a clean root project with `pixi`-managed environments and a minimal package skeleton

Tasks:

- add root `pyproject.toml`
- define `pixi` workspace and environments
- create `src/flights_search/`
- create `tests/`
- add baseline `README.md`
- add formatting, lint, typing, and test task definitions

Suggested initial module skeleton:

```text
src/flights_search/
├── __init__.py
├── api.py
├── models/
├── encoder/
├── client/
├── parser/
├── booking/
└── py.typed
```

Exit criteria:

- `pixi install` succeeds
- `pixi run test` executes an initial smoke test
- editable import of `flights_search` works

### Phase 2. Implement typed request and response models

Goal:

- define the stable internal and public model layer first

Tasks:

- implement request models:
  - `TripLeg`
  - `Passengers`
  - `FlightSearchRequest`
  - `SelectedSegment`
  - `SelectedLeg`
  - `SelectedItinerary`
  - booking request model if kept separate from `SelectedItinerary`
- implement response models:
  - `Airport`
  - `FlightSegment`
  - `FlightOption`
  - `CarbonData`
  - `SearchResults`
- include an opaque continuation handle on parsed results or selected options so round-trip follow-up can be built without exposing raw `tfu`
- add validation rules where needed
- decide which fields remain internal-only and are excluded from public constructors

Important rule:

- public models should not expose raw `tfs`, `tfu`, or payload indexing concepts
- public selection models must support multi-segment legs; they cannot assume one segment per leg

Exit criteria:

- the public API vocabulary is stable enough for encoder, parser, and booking work

### Phase 3. Build the encoder subsystem

Goal:

- convert typed requests into Google Flights transport data without mixing network or parsing logic

Tasks:

- migrate or reimplement protobuf-backed request encoding
- isolate generated protobuf artifacts under the encoder subsystem
- implement one-way request encoding
- implement round-trip request encoding
- implement selected-outbound follow-up encoding from an opaque continuation handle or selected outbound option
- implement final selected-itinerary booking request construction
- support selected-leg encoding for both single-segment and multi-segment itineraries
- add small, focused tests for encoded parameter generation

Outputs:

- transport parameter builder for initial search
- transport parameter builder for follow-up search
- transport parameter builder for booking-resolution inputs

Exit criteria:

- encoding behavior for one-way and round-trip flows is covered by tests

### Phase 4. Build the HTTP client subsystem

Goal:

- provide a narrow, explicit retrieval layer for Google Flights HTML and any booking-related page content

Tasks:

- choose the HTTP client library
- define a minimal client interface
- implement search page retrieval
- define headers, retries, timeout defaults, and error handling
- require support for the request behavior Google Flights currently expects in practice, including browser impersonation or an equivalent strategy, referer handling, and cookie persistence if needed
- keep follow-up retrieval logic separate from parser concerns

Suggested responsibilities:

- `fetch_search_html(request_params) -> str`
- optional booking-page retrieval helpers if HTTP-only extraction is useful

Exit criteria:

- encoder output can be passed to the client and produce retrievable HTML fixtures

### Phase 5. Build the parser subsystem for initial results

Goal:

- parse initial Google Flights responses into strong typed results

Tasks:

- define how representative HTML fixtures will be captured from the direct client flow and sanitized for repository use
- extract the embedded callback payload from the HTML
- locate and normalize airline metadata
- parse initial search result rows
- map raw payload positions into typed model builders
- add fixture-based tests for parser stability

Important rule:

- raw payload indexing should remain private to parser internals

Exit criteria:

- a one-way search fixture can be parsed into `SearchResults`

### Phase 6. Add follow-up selected-itinerary parsing

Goal:

- support the second-step flow used after a user chooses an outbound option

Tasks:

- implement parsing for follow-up response shape
- model the return-option response as typed results
- preserve the follow-up continuation information needed by the next step behind an opaque typed field or helper-owned handle
- verify selected-outbound round-trip behavior against legacy semantics
- add fixtures for follow-up flows

Exit criteria:

- round-trip return options can be parsed after supplying an outbound selection

### Phase 7. Build the booking subsystem

Goal:

- resolve booking URL candidates from an explicit selected itinerary without mutating search results as a side effect

Tasks:

- define a booking request model or builder API
- implement `build_booking_request(...)`
- implement `get_booking_urls(request)`
- optionally implement `get_booking_url(request)` as a convenience helper
- reuse HTTP-only extraction if feasible
- keep Playwright fallback scoped only to booking resolution
- return best-effort results and allow an empty list when nothing is extractable
- accept selected itineraries composed of one or more segments per leg

Important rule:

- search APIs must not trigger booking resolution implicitly

Exit criteria:

- one-way and round-trip selected itineraries can resolve zero or more booking links

### Phase 8. Expose the public package API

Goal:

- provide a minimal top-level surface consistent with the plan

Expected exports:

- `FlightSearchRequest`
- `TripLeg`
- `Passengers`
- `SelectedSegment`
- `SelectedLeg`
- `SelectedItinerary`
- `SearchResults`
- `search_flights`
- `build_booking_request`
- `get_booking_urls`

Optional export:

- `get_booking_url`

Tasks:

- implement package-level exports in `src/flights_search/__init__.py`
- keep internal subsystems out of the primary public API
- verify public import ergonomics in tests

Exit criteria:

- the root import path matches the new API goals and excludes legacy aliases

### Phase 9. Finalize docs and examples for the new surface only

Goal:

- replace legacy-oriented explanations with clear docs for the greenfield package

Tasks:

- update root `README.md`
- document one-way search flow
- document round-trip follow-up flow
- document explicit itinerary selection before booking resolution
- keep internal transport details out of public docs

Exit criteria:

- docs describe only the new supported API

## Testing Strategy

The test suite should be organized around user-visible flows and subsystem contracts.

### Unit tests

- request model validation
- encoder output generation
- parser helpers for payload extraction and normalization
- booking request construction

### Fixture-driven integration tests

- one-way search HTML -> `SearchResults`
- round-trip initial search HTML -> outbound options
- follow-up round-trip HTML -> return options
- booking payload extraction for one-way itinerary
- booking payload extraction for round-trip itinerary
- multi-segment itinerary selection can be encoded for follow-up and booking flows

### Public API tests

- `search_flights(request)` returns typed `SearchResults`
- booking APIs require explicit itinerary selection input
- search APIs do not mutate results with booking URLs
- legacy aliases are not exposed

### Tooling checks via `pixi`

- lint passes
- type checking passes
- tests pass under the default supported Python version

## Fixture Strategy

Representative fixtures should be planned as part of implementation, not treated as incidental test data.

Required fixture categories:

- one-way search HTML captured from the direct Google Flights client flow
- round-trip initial search HTML with outbound continuation data present
- round-trip follow-up HTML for return options
- booking response samples for one-way and round-trip resolution
- at least one multi-segment itinerary example if a stable sample can be captured

Fixture rules:

- commit sanitized fixtures to the repo for deterministic parser and booking tests
- keep a small manifest documenting what each fixture represents and which flow it covers
- prefer raw-enough fixtures to detect payload-shape regressions, while removing unnecessary personal or session-specific data where possible
- do not block the architecture phase on capturing every fixture, but do make fixture capture an explicit task before parser and booking phases deepen

## Proposed Execution Order

1. Write `.docs/core-architecture-redesign.md`.
2. Bootstrap root packaging and `pixi` environments.
3. Create typed request and response models, including the continuation-handoff design and multi-segment selection shape.
4. Capture and sanitize the first parser fixtures from the direct retrieval path.
5. Implement one-way encoder support.
6. Implement search HTTP retrieval.
7. Implement initial-response parsing.
8. Implement outbound-selection follow-up encoding.
9. Implement follow-up response parsing.
10. Implement booking request building and booking-link resolution.
11. Expose the top-level API.
12. Finalize tests, remaining fixtures, and documentation.

## Risks And Mitigations

### Google Flights payload volatility

Risk:

- parser or encoder assumptions may break as payload structure changes

Mitigation:

- isolate raw indexing in parser internals
- use HTML fixtures for regression detection
- keep model mapping logic covered by focused tests

### Follow-up token handoff ambiguity

Risk:

- round-trip follow-up support could stall if the initial search results do not carry enough opaque information to build the next request without leaking transport details

Mitigation:

- lock the continuation-handoff design in the architecture spec before model and encoder work deepens
- test the full outbound-selection to return-options flow using committed fixtures

### Multi-segment itinerary under-modeling

Risk:

- an API built around one selected segment per leg will fail for connecting itineraries and force a public model redesign later

Mitigation:

- define a selected leg as an ordered collection of selected segments from the start
- include multi-segment coverage in encoder and booking tests

### Booking-link extraction instability

Risk:

- booking links may not always be available through static retrieval alone

Mitigation:

- keep browser automation isolated inside `booking/`
- support empty results as a valid best-effort outcome
- test HTTP-first and browser-assisted paths separately where possible

### Scope drift from legacy features

Risk:

- vendor integrations, helper enums, or compatibility shims could expand the build unnecessarily

Mitigation:

- treat them as explicitly out of scope unless separately approved
- keep the architecture spec authoritative for first-build scope

### Tooling split between root and legacy

Risk:

- developers may accidentally keep using legacy environments or commands

Mitigation:

- centralize all active commands under root `pixi`
- document root workflows clearly in `README.md`
- avoid adding new build logic under `legacy/`

### Missing or weak fixtures

Risk:

- parser and booking work may proceed against ad hoc samples that do not cover the real payload shapes we need to support

Mitigation:

- make fixture capture and sanitization an explicit tracked deliverable
- keep a small set of representative committed fixtures for one-way, round-trip, follow-up, and booking flows

## Definition Of Done

This implementation plan is complete when the repo has:

- a root `pixi`-managed Python package
- a locked architecture spec in `.docs/core-architecture-redesign.md`
- a working typed search API
- explicit selected-itinerary booking resolution APIs
- tests for one-way, round-trip, and booking flows
- documentation that reflects only the new supported surface

## Recommended First Implementation Slice

The first coding slice after this planning step should be:

1. write `.docs/core-architecture-redesign.md`
2. create root `pyproject.toml` with `pixi` configuration
3. scaffold `src/flights_search/` and `tests/`
4. implement request/response models, including opaque continuation handoff and multi-segment selection modeling
5. capture the first search fixtures from the direct retrieval path
6. add encoder tests before wiring network and parser logic

This sequence keeps architecture decisions stable before public models harden, starts `pixi` early, and makes fixture capture explicit before parser and booking work deepen.
