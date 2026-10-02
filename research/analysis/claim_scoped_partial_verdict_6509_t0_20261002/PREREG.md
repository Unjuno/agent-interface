# Issue #6509 T0 allocation — frozen before container invocation

Status: **FROZEN, candidate/auditor not yet invoked**. Origin: [Issue #6509](https://github.com/Unjuno/agent-interface/issues/6509). This is the first explicit T0 for the issue; it does not repeat the earlier in-memory exploratory enumeration. It adds the two unresolved freeze cases from the latest Issue comment.

## H / T / D / C / U

**H.** A claim-scoped verdict ladder can retain an early source-bound decisive negative or deadline-useful `PARTIAL_UNKNOWN` while never promoting partial positive evidence, stale evidence, contradictory receipts, or incomplete mandatory coverage to `ALLOW`. A durable receipt can survive crash/recovery without duplicate commit, while a torn receipt never counts as completed coverage.

**T.** Deterministic no-model scheduler/receipt harness, 15 frozen traces × 3 policies (`ALL_OR_NOTHING_TIMEOUT`, `UNSAFE_SCALAR_PROGRESS`, `CLAIM_LADDER`) = 45 rows. Mandatory DAG: identity (1 ms), freshness (2 ms), effect (8 ms); optional diagnostic (3 ms); deadline 12 ms. Cases cover complete positive, partial positives at two cut points, decisive identity negative, freshness negative, generation change, dropped mandatory check, same-generation contradiction, torn receipt, crash after durable receipt before commit, duplicate recovery replay, new-generation contradiction, diagnostic pending after mandatory coverage, wrong claim scope, and cutoff before effect. The full allocation table is `scenarios.json`. Candidate is one Python process in one network-disabled OrbStack container; raw-only independent auditor is one separate container invocation after candidate exit 0. Source is mounted read-only, output in a unique host directory, root filesystem read-only, bounded CPU/memory/PIDs. Python image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/arm64. No GPU, model, GUI, user data, external effects, or network.

**Receipt and consumer semantics frozen from the open clarification gate:** A durable receipt is append-only and may be replayed idempotently after a crash; a receipt that is not durable is excluded. Recovery rechecks exact claim and evidence generation before use. Opposing values for the same check, claim, and generation yield `PARTIAL_UNKNOWN`; a receipt from another generation or claim also yields UNKNOWN. Only identity/effect negative receipts are designated decisive for early counterexample, and only while source-current and contradiction-free. Freshness-negative, stale, missing, deadline-cut, or partial-positive traces do not ALLOW. A complete verdict requires all mandatory checks. All outputs remain descriptive, non-authoritative; consumer side effects are fixed at zero.

**D.** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs all 45 policy/trace rows and receipt histories; rejects any partial-positive ALLOW, stale/wrong-scope or contradictory promotion, counts no torn receipt toward coverage, reconstructs durable crash replay exactly once, records zero authority and side effects, confirms the unsafe scalar control exposes partial-positive counterexamples, and rejects four raw mutations. Any unsafe ladder ALLOW or missing mandatory check is FAIL; serialization/hash/audit failure is STOP. Report time-to-counterexample/YIELD only as simulated logical milliseconds; no measured wall-clock benefit is claimed.

**C.** All-or-nothing timeout may be simpler and equally fast; an exact-scope conservative policy may return UNKNOWN for nearly every incomplete trace. Deterministic service costs omit real scheduling and durable-storage latency.

**U.** Finite authored traces cannot establish GUI verifier truth, actual persistence/crash consistency, model quality, actual deadlines, real safety, authority, or product performance. The eventual T1 requires a separately frozen disposable target and allocation.

## Freeze identities and run boundary

- Allocation: `claim-scoped-verdict-6509-t0-20261002-01`
- Branch: `research/claim-scoped-verdict-6509-t0-20261002`
- Additive path: `research/analysis/claim_scoped_partial_verdict_6509_t0_20261002/`
- Base `main`: `900c48368909a247ffd2b1b4dddd944cd6008d90` (current at the final
  pre-run check). The earlier `f6c6d2004` freeze was not executed; main advanced
  before candidate invocation. Its intervening changes were merged unchanged
  into this branch, and the candidate/auditor/fixture hashes stayed identical.
- Source files: `candidate.py`, `audit.py`, `scenarios.json`; source SHA-256 values are recorded in `FREEZE.json` before formal invocation.
- Construction unit tests: `test_harness.py`, run before freeze. No candidate/auditor formal invocation occurred during construction.
- Candidate output path `results/allocation-01/` must be absent/empty before invocation. Candidate and auditor have separate container calls. No retries. Preserve first stdout, stderr, process exit and output bytes.
