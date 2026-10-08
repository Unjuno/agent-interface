# Accepted begin to execution receipt causality — #5215

Worker: `01a0ff58-480b-7d50-9eee-0bce12250476`, FINAL-v5.
Pinned main: `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`.
Branch: `research/kernel-begin-causality-01a0ff58-20261003`.
This is a new ordinary engineering boundary check, not a formal allocation or a rerun of #5216.
Historical #5215/#5225/#5229 bytes and outcomes remain immutable.

- H: identity matching alone permits an execution receipt to start before the accepted begin event. Keeping that event's timestamp allows refusal of this contradiction.
- T: test-first reproduction; exact Git source snapshots; isolate one subclass adding the remembered lower bound; enumerate begin 1..4, receipt start 0..5, receipt end start..6, and valid/invalid manifest identities (216 rows per arm). Independently reconstruct every row from raw with a stdlib auditor importing no candidate, kernel, fixtures or producer. Test altered/missing/duplicate/type-corrupted rows. Check rejected begin, same-tick equality, later release/delivery and identity refusal.
- D: baseline gap is accepted pre-begin start under matching identity. Candidate passes this scoped gate only if every earlier start is refused without state mutation, all matching same/later starts remain accepted, manifest mismatches remain refused, and required row coverage/corruption checks pass. Unexpected exceptions or incomplete provenance are HOLD.
- C: all timestamps are authored exact integer nanoseconds in one synthetic clock. Equality provides no within-tick ordering. Late end/release/delivery is intentionally representable; no action cutoff is inferred.
- U: sequential, one accepted begin per lifecycle; no backend clock provenance, physical release, actual effect, thread safety, public MCP behavior, benefit, reliability or performance claim. The isolated subclass is an engineering candidate, not a promoted runtime repair. Duplicate begin and stale cancellation are separately owned by #6852/#6864.

CPU/stdlib only, one small process at a time. No shared resource, container, GPU, model, GUI or input is required. No edit to runtime/kernel. Common fleet deadline has not yet been confirmed; that uncertainty does not block this finite local check.

The row count is derived as 4 begin choices × (7+6+5+4+3+2 end choices) × 2 manifest choices = 216. Two arms yield 432 observations. Output is bounded below 1 MiB; each subprocess has a 60-second construction timeout.
