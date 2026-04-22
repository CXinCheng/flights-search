# Docs Index

This folder separates design, closeout guidance, and current status for the
root `flights_search` package.

## Reading Order

1. `core-architecture-redesign.md`
   The target system design and public API boundaries.
2. `implementation-plan.md`
   The maintenance-mode closeout checklist for the limited work that remains.
3. `implementation-progress.md`
   The current implementation status based on the code and tests in this repo.

## Document Roles

### `core-architecture-redesign.md`

Use this when deciding whether a code change matches the intended package
shape, model boundaries, and search-versus-booking split.

### `implementation-plan.md`

Use this when deciding the small amount of validation and documentation work
that still remains now that the core feature surface is implemented.

### `implementation-progress.md`

Use this when you need to know what is already implemented, what has already
been live-tested, what tests currently exist, and which closeout items remain.
