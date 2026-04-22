# flights-search

Typed Python package for two focused Google Flights workflows:

1. search flights from a structured request
2. resolve booking URL candidates for an explicit selected itinerary

The active implementation lives at the repository root. The `legacy/` directory
is reference material only and is not the supported package surface.

## Status

The intended feature surface is implemented for the current project scope.
The repo is now in closeout and maintenance mode:

- the initial search flow is implemented
- the round-trip follow-up flow is implemented
- explicit itinerary booking URL resolution is implemented
- unit coverage is committed for the implemented runtime slices
- representative live validation has been completed

The main remaining work is limited to broader live validation across more route
shapes and deciding whether to commit any sanitized live fixtures for
regression protection.

## Planned Package Shape

```text
src/flights_search/
tests/
pyproject.toml
```

## Development

`pixi` is the intended source of truth for environments and common tasks.

Available tasks:

- `pixi run test`
- `pixi run test-unit`
- `pixi run lint`
- `pixi run typecheck`
- `pixi run format`
- `pixi run docs-check`

The root package now includes the typed model layer, internal request
encoding, the initial and follow-up search runtime paths, and a
Playwright-backed booking-resolution flow for explicit selected itineraries.

For current implementation status and closeout notes, see:

- `.docs/implementation-progress.md`
- `.docs/implementation-plan.md`

Booking resolution needs the Playwright Chromium browser binary in addition to
the Python dependency. After installing dependencies, run
`python -m playwright install chromium` before calling `get_booking_urls(...)`
or `get_booking_url(...)`.
