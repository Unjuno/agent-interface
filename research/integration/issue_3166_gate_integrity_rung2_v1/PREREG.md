# Issue #3166 — gate-integrity successor rung 2

Allocation: `issue3166-gate-integrity-rung2-20260927-01`.
This is additive to, and does not rewrite, the already-consumed rung1 in
`issue_3166_fresh_gate_truth_v1/` and PR #4506.

## H / T / D / C / U

**H — Hypothesis.** A two-tier admission comparator that independently checks
the prepared dependency snapshot and a fresh, typed, source/target/lineage/
intent/epoch-bound TRUE receipt refuses all eight invalid evidence contexts in
the frozen matrix before input. Reduced comparators produce at least one
observable GTK effect on invalid evidence. Replaying an identical accepted
commit is either refused before a second effect or recorded as a scoped
duplicate-replay failure. A partial/collateral receipt is never scored as exact
task success.

**T — Treatment.** Freeze current `main` at
`2c5be06f9563deb3e5e739df6e7f154d145a8687`. Run the repository's pinned
`runtime.cli_v1.golden_v3.dispatch_golden_v3` through its X11 backend against
the retained GTK3 fixture. The matrix has 10 contexts × 4 comparators = 40
rows: current valid evidence; stale dependency version with the GTK target
still alive; fresh FALSE; fresh UNKNOWN; stale TRUE; mismatched source lineage;
missing lineage; malformed timestamp type; cross-intent receipt; and
cross-epoch receipt. Comparators are TWO_TIER_FRESH_GATE, DEPENDENCY_ONLY,
GATE_ONLY, and CACHED_PREPARE_GATE. Then run two identical dispatch attempts
with the same program/intent/epoch/receipt against one live fixture, and one
valid-admission `partial` fixture control that emits an exact-looking save plus
collateral data. Total: 43 retained records. All admitted matrix rows execute
the same real Ctrl+S GTK action; refusal must have zero runtime calls/emissions.

The independent oracle separately validates the complete prepared snapshot,
gate receipt bindings and timestamps, all policy decisions, target liveness,
runtime emissions/releases, event traces, exact effects, duplicate behavior,
and contradictory-control classification from raw JSONL. Formal result and
audit run in separate containers from a fresh evidence directory.

**D — Decision gates.** `PASS_GATE_INTEGRITY_RUNG2_SCOPED` only if all 40 cells
exist exactly once and match the independent oracle; TWO_TIER denies every
invalid case before runtime; each reduced comparator has an unsafe admission
witness with a verified GTK effect; all admissions have verified releases and
the exact `{"saved":true,"text":""}` effect; duplicate replay is refused
without a second save; the contradictory control is explicitly not task
success; cleanup and source/result hashes verify; and the independent audit has
zero errors. Any admitted unsafe action or duplicate replay yields a FAIL
finding. Missing/ambiguous postcondition, lineage, cleanup, or raw evidence is
HOLD. Provenance, container, fixture, or preformal infrastructure failure is
STOP, not a scientific result. One formal allocation; zero reruns and zero
post-freeze tuning.

**C — Constraints.** Use only OrbStack/Docker, cached image
`agent-interface-2994:20260920` (`sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`,
linux/arm64), network none, read-only repository/study mounts and rootfs,
dropped capabilities, no-new-privileges, bounded CPU/memory/PIDs, disposable
Xvfb/GTK, and a fresh writable evidence mount. No host display, real user
input, model/provider, credentials, GPU, external network, or runtime source
changes. Construction checks are not formal results.

**U — Unknowns / scope.** The four policies remain experiment comparators;
the current runtime does not expose a general commit-gate API. Receipt mutation
does not simulate races during model wait, IPC, or OS delivery. A PASS applies
only to this GTK/Xvfb fixture and frozen evidence transitions; it is not a
general GUI, browser, model, production-safety, cross-platform, or integrated
product claim. Issue #3166 remains open for any untested original acceptance
scope.

## Preservation

Do not rerun rung1 or alter PR #4506/#3185 evidence. Do not replace or pool
formal rows. Keep all FAIL/HOLD/STOP evidence. No issue closure is authorized by
this rung alone.
