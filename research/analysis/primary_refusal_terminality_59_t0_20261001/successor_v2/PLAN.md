# Issue #59 successor T1 — parse/presentation failures latch STOP

## Lineage and H / T / D / C / U

This is a separately frozen successor to parent T0, which retained
`FAIL_UNCERTAIN_DELIVERY_REPLAY`. T0's raw, audit, and source are immutable.

**H.** Moving response-envelope validation/parsing into the caller's same
fail-closed boundary as `sendPresented` prevents continuation after uncertain
delivery, while preserving explicit refusal feedback and allowing only public
close after a fault.

**T.** Freeze a small caller-boundary candidate with four mock cases:
(1) explicit refusal with original text/image; (2) malformed returned envelope
followed by a primary-like retry attempt; (3) valid completed input with a
verified neutral release; and (4) thrown transport/presentation error followed
by a retry attempt. Retain exact host-call order and stop state. An independent
raw-only auditor checks the result without importing the candidate.

**D.** `PASS_PARSE_FAILURE_TERMINALITY_CONSTRUCTION` iff explicit refusal,
malformed envelope and thrown transport error all latch STOP before any second
effectful host call, close remains allowed, original explicit-refusal content
is presented unchanged, and a valid input remains usable. Any post-fault input
dispatch is FAIL. The experiment is construction evidence only.

**C.** A more permissive continuation could improve task completion if an
authenticated transport proves pre-dispatch refusal. No such proof or typed
exception exists in the subject contract, so this candidate fails closed.

**U.** Deterministic host-only JavaScript mocks. No live MCP, GUI/X11, OS input,
effect, model, protocol relay, or end-to-end integration claim. The fix must be
reviewed and independently integrated into a later caller before any live
allocation.

## Freeze

- Allocation: `59-primary-refusal-terminality-host-t1-20261001-02`.
- Base main after preformal refreeze: `975aed8ad7923a109cfb445b4028d18a10088f63`.
- Current PR #5639 head: `5fc859f40dcd1bf39aaa9a2f5a78425c47a717cb`.
- Parent T0 subject: PR #5639 `9c7735a8c890e77fb9c51c6c4e93addeeba3158b`;
  source blob rechecked byte-identical at the current PR head.
- Host Node `v26.7.0`, built-ins only; network disabled by test design; no
  container due shared resource coordination under #5085.
- Construction command `node test.mjs` is preformal only.
- Candidate `node run.mjs > raw.jsonl` exactly once; audit
  `node audit.mjs raw.jsonl > AUDIT.json` exactly once.
- No retries, tuning or edits after candidate invocation.
