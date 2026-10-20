# Architecture proposals

This directory holds reviewed or reviewable architecture proposals. A proposal
does not change runtime behavior or grant experiment resources. Keep its status,
source revision, evidence links, unresolved decisions, and validation boundary
explicit; move a proposal into implementation only after those decisions are
resolved.

## Prestarted cancellation supervisor

[`PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md`](PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md)
proposes a bounded, prestarted Fake X cleanup supervisor for the opt-in owned
`guarded-x11` caller. It is based on the current-main source audit and existing
Fake X / Xvfb evidence. It does not establish a live-X guarantee, task success,
MAP01, physical desktop control, WSLc allocation, or integrated efficiency.

The next validation boundary is a public-MCP Fake X composition test: preserve
the original action result separately from the cancellation-operation receipt,
keep cancel requests idempotent, and refuse late/stale-generation effects. The
300 ms response and 3 s transaction values in the proposal are provisional test
targets, not approved compatibility promises. The proposal is not a runtime
implementation assignment.
