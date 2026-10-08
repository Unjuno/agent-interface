# Issue #6689 T0 — prefix-stability certificates

Status: executed once; `FAIL_AUDIT` / `STOP_CLASSIFICATION_COUNT_CONTRACT`.
No runtime, GUI, model, provider, task input, action authority, or product
behavior is under test. This is not a method pass.

## H / T / D / C / U

**H — hypothesis.** In the frozen finite asynchronous evidence model, an
independent all-continuations oracle can distinguish (a) a stable terminal
disposition, (b) a provisional prefix, (c) a positive-looking prefix whose
optional source frontier is still open, and (d) an invalid/unmodeled prefix.
It will find a source-current decisive mandatory failure that is stable before
all sources finish, while no PASS is finalized before mandatory coverage and
the optional finite source's explicit completion event.

**T — minimum test.** Enumerate 40 worlds formed by two mandatory verifier
outcomes, one generation-validity outcome, and five optional-source paths.
Enumerate every source-order-respecting interleaving and every event prefix.
The candidate computes certificates from the frozen universe; a separate
raw-only oracle independently constructs legal continuations and terminal
dispositions. Compare every unique prefix, then require four corruption
controls (drop a mandatory event, forge source closure, relabel stale/current,
and treat timeout as completion) to be rejected. Compare logical finalization
points with wait-for-all and a fixed event-count deadline; these are model
positions, not wall-clock latency.

**D — decision.** `PASS_METHOD_SCOPED` only if the source/spec hashes match,
candidate and independent oracle agree for every prefix, all four mutation
controls are rejected, at least one source-current mandatory FAIL is stable
before all sources close, no PASS is stable while any mandatory check or the
optional frontier is incomplete, and every row grants zero authority/effects.
Any false stable result or missing required negative/frontier case is
`FAIL_METHOD`; an unspecified legal-continuation contract or incomplete audit
is `HOLD/UNKNOWN`. Actual stop rule: candidate row-level counts agree with the
oracle, but the candidate header's `classification_counts` includes synthetic
`EARLY_STABLE_*` metric keys while the auditor independently counts only
classifications. The auditor therefore exits nonzero; no repair or rerun is
permitted under this allocation.

**C — competing explanation.** Wait-for-all or a claim-scoped deadline may be
equally useful and simpler. The earlier #6509 ladder already establishes a
scoped early-negative/partial-verdict result; this T0's distinct question is
whether an exhaustive prefix-to-all-legal-continuations certificate can prove
stability, particularly around explicit source closure. The experiment does
not claim a broader benefit over #6509.

**U — uncertainty.** The event universe is authored and finite; sources are
append-only within one immutable generation. The model excludes real late
corrections, scheduler behavior, source outages beyond the explicit timeout,
external GUI change, actuation freshness, and verifier truth. A stable evidence
disposition is not an authorized or still-fresh action.

## Frozen model boundary

Claim scope is one evidence-only claim at generation 7. Mandatory sources are
`target` and `effect`; a source-current result is either PASS or FAIL. A
separate `generation` source reports CURRENT or INVALID. An optional source may
report a clear prefix then a later conflict, complete with no conflict, or
timeout without a completion certificate. Source-local event order is fixed;
events from different sources may interleave arbitrarily. No event after a
source's terminal marker is legal. An observed valid mandatory FAIL is
decisive only once generation CURRENT is observed. PASS requires both
mandatory PASS results and optional COMPLETE with no conflict. Missing,
invalid, stale, or timed-out evidence is UNKNOWN. Nothing in this reducer
authorizes an external effect.

## Execution

The issue's T0 is a deterministic standard-library finite model with no
container-dependent semantics and requests no resource allocation. WSLc is
unavailable in this macOS environment; therefore this one exact CPU-only
enumeration is run natively, with its runtime recorded. No Docker/OrbStack
daemon is queried or used. The formal candidate and independent auditor each
run once; retries are zero. Construction tests run before the source freeze.

Commands are recorded in `FREEZE.json`; formal outputs go only under
`results/formal-01/`. The old #6509 result and all prior evidence remain
unchanged.
