# Flights Search Implementation Plan

## Purpose

This document records the remaining closeout checklist for the greenfield
`flights_search` package. The main feature surface is already implemented and
the project should be treated as feature-complete for its intended scope unless
live validation exposes a concrete blocking gap. For current repo status, use
`.docs/implementation-progress.md`.

## Scope

The package is being built around two product capabilities only:

1. search Google Flights from a structured request
2. resolve booking URL candidates for an explicitly selected itinerary

The `legacy/` tree can still be used for behavior discovery and fixture
research, but it is not a compatibility target.

## Delivered Surface

- root package at `src/flights_search/`
- stable public typed API
- request and result models
- encoder subsystem for initial, follow-up, and booking flows
- HTTP client subsystem for Google Flights retrieval
- parser subsystem for initial and follow-up results
- booking subsystem for selected-itinerary link resolution
- representative fixtures and automated tests
- focused docs for architecture, plan, and current progress

## Current Position

The planned major features are implemented:

- structured search request encoding
- initial search result parsing
- round-trip follow-up search flow
- selected-itinerary booking request generation
- booking URL resolution through the explicit booking API
- automated unit coverage for the implemented runtime slices

The project should not keep expanding the feature surface unless live testing
reveals a concrete gap that blocks one of the two intended product
capabilities.

## Remaining Closeout Work

### 1. Extend live validation slightly

Goal:
Verify that the implemented runtime slices still behave correctly against real
Google Flights responses.

Tasks:

- run live one-way search validation on representative routes
- run live round-trip follow-up validation after selecting outbound options
- run live booking resolution validation for selected itineraries
- note any response-shape mismatches, anti-bot issues, or environment
  prerequisites such as Playwright browser installation

Exit criteria:

- the core search and booking flows are exercised against live responses
- any issues found are classified as blockers, minor fixes, or acceptable
  operational constraints

### 2. Capture minimum regression evidence

Goal:
Preserve enough real-world evidence to support the current implementation
without reopening broad feature development.

Tasks:

- capture sanitized live HTML and booking-result payload samples when stable
- confirm whether existing synthetic fixtures are sufficient once compared
  against live payloads
- add only the minimum extra fixture coverage needed for confidence

Exit criteria:

- live behavior has been compared against the current parser and booking logic
- fixture coverage is good enough to protect the implemented feature set

### 3. Keep docs in maintenance mode

Goal:
Reflect that the package has reached implementation completion for the intended
scope and move the repo into maintenance mode.

Tasks:

- update `.docs/implementation-progress.md` after live testing
- trim this plan so it no longer reads like an open feature roadmap
- update `.docs/README.md` to point readers to status and maintenance guidance
- make any final README usage or environment notes that live testing proves
  necessary

Exit criteria:

- docs clearly state that the major feature work is complete
- remaining work is framed as validation and maintenance, not new feature
  delivery

## Completion Signal

Once the remaining validation is judged sufficient, this repo should be treated
as complete for the current scope and maintained through targeted fixes rather
than new feature expansion.

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
- additional feature expansion beyond the current search and booking scope
