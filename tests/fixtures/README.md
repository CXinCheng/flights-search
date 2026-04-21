# Test Fixture Notes

This directory now serves two purposes:

1. record stable test inputs for the current encoder/model slice
2. document the response payload shapes we expect the parser slice to handle

## What Is Recorded Now

- `encoder_cases.json`
  - human-readable request descriptions for the current encoder tests
  - exact expected query params, including `tfs` and `tfu` where applicable
  - includes:
    - one-way initial search
    - round-trip follow-up search
    - one-way booking request
    - round-trip booking request
- `payloads/one_way_initial.json`
  - synthetic example of an initial search payload
  - rows live at `payload[2][0]`
- `payloads/round_trip_follow_up.json`
  - synthetic example of a follow-up return-options payload
  - rows live at `payload[3][0]`

## Important Parser Notes

- Initial search responses use the row list under `payload[2][0]`.
- Follow-up round-trip responses use the row list under `payload[3][0]`.
- Airline and alliance metadata is shared across both shapes and lives under:
  - alliances: `payload[7][1][0]`
  - airlines: `payload[7][1][1]`

This distinction is important for scraping because the parser cannot assume a
single row offset for every Google Flights response.

## Why The Response Fixtures Are Synthetic

The current repo slice does not yet include the final browser-like client
behavior needed to capture reliable live Google Flights result pages. We can
reach Google Flights from the environment, but a simple direct request still
returns the unsupported shell instead of a stable results payload.

To keep implementation moving without baking in misleading live samples, the
committed response fixtures here are minimal synthetic payloads that document
the structure discovered in the legacy parser and test analysis.

## What We Still Need Later

- one-way live search HTML
- round-trip initial live search HTML with continuation data
- round-trip follow-up live HTML for return options
- booking-response samples for one-way and round-trip selection
- at least one multi-segment itinerary example if stable

## Sanitization Rules For Future Live Fixtures

- remove personal identifiers and session-specific cookies where possible
- keep payload structure intact enough to catch parser regressions
- document whether a fixture is initial search, follow-up, or booking related
- record the request that produced the response so parser work is explainable
