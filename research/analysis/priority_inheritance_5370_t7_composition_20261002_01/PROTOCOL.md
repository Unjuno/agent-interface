# Frozen method protocol

## H/T/D/C/U

**H.** In this finite scheduler, composition of authenticated live blocking-chain inheritance, cycle refusal, a per-holder boost cap, cancellation/release, and a medium-service bound reduces verifier deadline misses on acyclic complete inversion cases versus `DEADLINE_ONLY`, without stale admission or unauthorized inheritance.

**T.** Twelve authored scenarios × three policies (`DEADLINE_ONLY`, `NAIVE_UNBOUNDED_PI`, `COMPOSED_BOUNDED_PI`) produce 36 rows. Scenarios cover direct/nested chains, cycle attempt, holder cancellation, claim expiry, forged urgency, incomplete/non-live blocker information, caps below/at/above needed work, an infeasible verifier deadline, and medium service after the cap. The source and scenario JSON are frozen by SHA-256. Candidate and separately implemented raw-only auditor each run exactly once in distinct network-disabled OrbStack containers using the cached digest-pinned CPython 3.12 image; retries=0. Source/input mounts are read-only; outputs are isolated.

**D.** `PASS_COMPOSITION_METHOD_SCOPED` requires 36/36 exact independent reconstructions, fewer composed-policy verifier deadline misses than `DEADLINE_ONLY` in the predeclared inversion subset, cycle refusal, no composed boost for unauthenticated/expired/incomplete/non-live claims, cancellation release, no stale admissions, at-most-one-tick delay to the first eligible medium service after cap exhaustion, and rejection of all nine corruption controls. Otherwise preserve the exact `FAIL_METHOD` or `STOP_*` disposition; never retry.

**C.** Hand-authored cases cannot exhaust asynchronous cancellation, hidden ownership, remote/non-preemptible resources, or arrival distributions. Candidate and auditor share a written specification; independent code and mutations reduce but do not eliminate common-mode error.

**U.** This is synthetic scheduler-method evidence only, not a production scheduling, authority-security, GUI, model, real latency, or user-safety result.

## Event semantics

Ticks are unit-cost service quanta. L owns R1; in nested cases M owns R2 and waits on R1; H waits on R1 (direct) or R2 (nested); B is unrelated medium work. Base priorities are L=1, M/B=2, H=3. Ties use fixed H>M>B>L ordering. A verifier result is admissible only if it finishes no later than its frozen deadline; otherwise it is `UNKNOWN_STALE`. Cancellation releases R1 before that tick's scheduling choice. Claim expiry immediately ends further inherited boosts; the base scheduler must still drain/release the finite holder work within the frozen horizon. A composed boost is allowed only for an authenticated, live, unexpired claim on a complete current wait chain and consumes the configured holder cap. A proposed edge that closes a wait cycle is refused by both safe policies; the intentionally naive arm admits it as a negative control. The candidate stops at 20 ticks.

The exact parameters are the `scenarios.json` bytes. Formal identity and source hashes are in `FREEZE.json`; formal commands and container facts are in `formal/` and `REPORT.md`.
