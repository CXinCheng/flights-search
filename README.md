# flights-search

Greenfield Python package for two focused Google Flights workflows:

1. search flights from a structured request
2. resolve booking URL candidates for an explicit selected itinerary

The active implementation lives at the repository root. The `legacy/` directory
is reference material only and is not the supported package surface.

## Planned Package Shape

```text
src/flights_search/
tests/
pyproject.toml
```

## Development

`pixi` is the intended source of truth for environments and common tasks.

Planned tasks:

- `pixi run test`
- `pixi run test-unit`
- `pixi run lint`
- `pixi run typecheck`
- `pixi run format`
- `pixi run docs-check`

The root package now includes the typed model layer, internal request
encoding, the initial and follow-up search runtime paths, and a
Playwright-backed booking-resolution flow for explicit selected itineraries.

Booking resolution needs the Playwright Chromium browser binary in addition to
the Python dependency. After installing dependencies, run
`python -m playwright install chromium` before calling `get_booking_urls(...)`
or `get_booking_url(...)`.
