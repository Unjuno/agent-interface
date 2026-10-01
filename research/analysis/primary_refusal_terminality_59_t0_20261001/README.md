# Primary refusal terminality — Issue #59

Retained fail-closed-boundary probe of PR #5639's experimental primary caller.
The explicit-refusal control stops correctly; an invalid response envelope
throws without latching STOP, allowing a primary-like caller to issue another
guarded input. See `PLAN.md`, `FREEZE.json`, `REPORT.md`, `raw.json`, and
`AUDIT.json`. This is mock-only construction evidence, not live integration.
