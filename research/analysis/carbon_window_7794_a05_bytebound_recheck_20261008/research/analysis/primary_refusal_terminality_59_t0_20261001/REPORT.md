# Issue #59 T0 — primary refusal terminality boundary

## Disposition

`FAIL_UNCERTAIN_DELIVERY_REPLAY`. The #5639 experimental caller latches STOP
after an explicit MCP refusal, but not when a returned response envelope is
malformed and its parser throws. A primary-like consumer that catches this
tool-call exception can make a second guarded-input call; the mock host accepts
that call. Since delivery of the first input is uncertain, the wrapper must
not allow that continuation.

This is a concrete caller-boundary failure in the experimental candidate, not
a claim that a live input was duplicated or that the production runtime has
the same bug. The candidate source and existing PR evidence are unchanged.

## Frozen experiment and result

- Issue #59; allocation `59-primary-refusal-terminality-host-t0-20261001-01`.
- Main base: `7f78c6131a23c0a1a9f6c388ab26a567e5f7dfdf`.
- Subject: byte-identical copy of PR #5639 `next-primary-policy.mjs` at
  `9c7735a8c890e77fb9c51c6c4e93addeeba3158b`, SHA-256
  `199e2a7f03716944191d292443d72e4b188a07e949529664ea07a58a5679a036`.
- Host: Node `v26.7.0`; deterministic mock host, no network/model/GUI/X11/input.
  Docker/OrbStack was not used because #5085 has other named/queued shared
  intervals and no exclusive lease for this allocation.
- Candidate invocation count 1; audit invocation count 1; no retry or tuning.
- The candidate command produced complete raw JSON, but its shell wrapper then
  failed while assigning zsh's reserved read-only variable `status`; therefore
  the candidate process exit status was not captured. The raw was not regenerated.
- The separate raw-only audit exited 1, retained in `AUDIT.json`.

| Case | Preserved response | STOP latched | Post-fault input | Close | Result |
|---|---:|---:|---:|---:|---|
| Explicit planned MCP refusal | yes (text+image) | yes | blocked before host | allowed | expected |
| Invalid response envelope | envelope passed to presentation boundary, no usable receipt | no | one extra guarded input reached host and returned success | allowed | unsafe continuation |

The raw retains exact host-call order. The independent auditor found four
errors in the malformed-envelope case: presentation classification mismatch,
STOP not latched, effectful retry not blocked, and post-fault host dispatch.
The presentation-classification discrepancy is a harness/audit labeling issue
for an invalid envelope; it does not negate the three independently visible
terminality failures in the raw call list and stop state.

## Construction defect and command note

The first preformal harness attempt failed because it did not catch the
subject's TypeError as a primary consumer would. That harness defect is retained
in `CONSTRUCTION_NOTES.md`; the candidate was not invoked in that attempt. The
corrected preformal test passed two characterization scenarios, including the
observed nonterminal malformed-envelope behavior.

The formal candidate did run once and wrote complete `raw.json`. The enclosing
zsh command then failed on `status=$?` because `status` is read-only in zsh; no
exit value was retained. This procedural loss is recorded, not backfilled by a
candidate rerun. The audit was executed once on the retained raw and returned
FAIL.

## Decision and next boundary

Do not run the full live allocation with this exact caller candidate. A
successor should put response parsing/shape validation inside the same
fail-closed boundary as `sendPresented`, latch STOP on any parse/presentation
failure, preserve raw response material if available, and allow only explicit
public close after the fault. Add regressions for malformed result, absent
content, refusal-with-image, incomplete release and throwing presentation.
Then freeze a new allocation and audit the source before any live adapter use.

No positive claim is made about current-main runtime, live refusal policy,
physical release, task completion, token/latency benefit, or human tempo. Issue
#59 remains open.
