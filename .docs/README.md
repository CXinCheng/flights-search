# Docs Index

This folder separates design, closeout guidance, current status, and MCP
integration planning for the root `flights_search` package.

## Top-Level Reading Order

1. `core-architecture-redesign.md`
   The target system design and public API boundaries.
2. `implementation-plan.md`
   The maintenance-mode closeout checklist for the limited work that remains.
3. `implementation-progress.md`
   The current implementation status based on the code and tests in this repo.
4. `mcp-server/implementation-plan.md`
   The implementation plan for exposing the package as an MCP server within
   this repository.
5. `mcp-server/implementation-progress.md`
   The current MCP-server-specific status and remaining work.

## Document Groups

### Core package docs

These documents describe the current `flights_search` package itself: its
architecture, implemented surface, and remaining closeout work.

### MCP server docs

These documents describe the planned adapter layer that will expose the current
package to another AI agent through MCP without re-implementing the domain
logic.

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

### `mcp-server/implementation-plan.md`

Use this when planning or reviewing the same-repo MCP server, including tool
scope, package shape, statelessness, schema design, testing, and rollout
phases.

### `mcp-server/implementation-progress.md`

Use this when tracking the actual implementation status of the MCP layer, what
has already been decided, what code has not been written yet, and what the next
practical implementation steps are.
