# Issue #6195 T1: retained-trace eligibility inventory

## H / T / D / C / U

**H:** At least one of the frozen v38/v39 retained traces contains an identity-joined, same-clock chain sufficient for a delay–gain evaluation: source capture, a decision explicitly bound to consumed-generation identity, actual held input with identity-bound verified release, independent task-relevant effect, and at least two correction opportunities. Missing endpoints produce an evidence-availability HOLD, not a claim about the live system.

**T:** Read-only inventory of exactly two SHA-pinned `events.jsonl` files. Candidate reports exact event counts, candidate endpoint rows, relevant field names, source hashes and six per-trace eligibility gates. A separately implemented raw-only auditor reconstructs the same summaries from raw bytes and rejects five altered candidate documents. No replay, model call, GUI/game, actuation, task effect, or causal comparison.

**D:** `T1_ELIGIBLE_TRACE_FOUND` only if at least one trace passes all six gates and the raw-only auditor independently reconstructs every field and rejects every mutation. Otherwise `HOLD_NO_CLOSED_LOOP_TRACE`. Hash/parse/reconstruction mismatch is retained as FAIL/HOLD; no retry.

**C:** This inventory covers only the two named retained logs and the explicitly required field/event identities. It may conservatively miss semantically equivalent evidence encoded under unrecognized fields; such evidence must be separately source-bound before changing the classification.

**U:** No actual key occupancy, applicable controller stability, independent useful feedback, task-effect causality, safety, MAP01 completion, human-tempo, or runtime claim. No conclusion transfers to GUI/DOOM behavior.

## Inputs and isolation

Frozen at current main `14b81dd1f6853623a694266b98538f812847257a`; the two Git blob IDs are in `FREEZE.json`. Local input copies are downloaded from `raw.githubusercontent.com` at that exact commit, then checked against the Git blob IDs before the window. Host CPU / Python 3.11.9 only; no GPU, Docker/WSL, network during candidate/audit, model, or user input. The candidate and auditor are each invoked once in the reserved 15-minute window; retries/substitutions=0.

