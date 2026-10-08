# Issue #59 T0 — refusal and malformed-response terminality

## H / T / D / C / U

**H.** After a live tool call returns an explicit planned refusal or an invalid
response envelope, the experimental primary caller must preserve/present the
original response where possible, latch STOP, prohibit every subsequent
effectful call, and still allow the public close operation. An invalid envelope
is uncertain delivery and must not be treated as permission to replay.

**T.** Exercise the frozen `next-primary-policy.mjs` from PR #5639 head
`9c7735a8c890e77fb9c51c6c4e93addeeba3158b` in two deterministic mock-host
sequences. First, return an explicit planned MCP refusal with text+image, catch
it as a primary might, attempt another guarded input, then close. Second, return
an invalid response envelope, catch the caller exception, attempt another
guarded input, then close. Record exact host calls, presented response count,
caller stop state, and errors. The audit consumes only the raw JSON.

**D.** `PASS_REFUSAL_TERMINALITY_CONSTRUCTION` iff both sequences present the
original refusal when one exists, send zero effectful calls after the first
refusal/fault, latch STOP, and permit close. Any post-fault effectful host call
is `FAIL_UNCERTAIN_DELIVERY_REPLAY`. The explicit-refusal case is a positive
control for the existing behavior.

**C.** A typed, authenticated planned-negative result could in principle permit
carefully bounded continuation, but this caller has no such typed contract; an
unrecognized error must therefore remain terminal. Negative-control arms can
be independently ended/closed rather than weakening the stop rule.

**U.** Host-local JavaScript mock only. It does not exercise MCP transport,
X11/GUI, model behavior, actual tool effects, runtime release, or the full
desktop/MAP01 route. The experiment is a concrete caller-construction blocker
probe for the next #59/#57 integrated allocation, not a live integration PASS.

## Freeze and resource boundary

- Base main: `7f78c6131a23c0a1a9f6c388ab26a567e5f7dfdf`.
- Subject: exact copy of `runtime/results/post-release-spine-05/next-primary-policy.mjs`
  from PR #5639 head `9c7735a8c890e77fb9c51c6c4e93addeeba3158b`.
- Node built-ins only; no network, model, GUI, X11, OS input, or external effect.
- No container: shared host has explicitly timed OrbStack allocations queued
  under #5085 (including #5550 00:50–01:05 UTC and #5521 01:50–02:05 UTC); no
  exclusive slot for this experiment is recorded. CPU host execution here is
  only a deterministic caller-boundary construction check.
- Candidate command: `node run.mjs > raw.json` exactly once.
- Independent audit command: `node audit.mjs raw.json > AUDIT.json` once.
- Construction tests are preformal only and do not count as candidate output.
- No retries, tuning, candidate replacement, or reuse of a different allocation.
- The first preformal `node test.mjs` attempt exited on the intentionally
  malformed-envelope TypeError because the test did not model the primary
  catching a tool exception. No candidate CLI ran. The harness was corrected
  to model that catch-and-continue boundary; this attempt is retained in
  `CONSTRUCTION_NOTES.md`.
