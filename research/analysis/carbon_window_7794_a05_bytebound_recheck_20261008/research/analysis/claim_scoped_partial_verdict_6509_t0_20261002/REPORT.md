# Issue #6509 T0: claim-scoped partial verdicts

**Disposition: `PASS_METHOD_SCOPED` for the frozen 15-trace deterministic model.**
The formal candidate ran once and the separate raw-only auditor ran once; no
retries. This is the Issue's first retained candidate experiment, not a repeat
of its earlier in-memory analyst precheck.

## Result

The one-shot candidate emitted 45 rows (15 traces × 3 policies). The independent
auditor reconstructed all 45, returned `PASS_METHOD_SCOPED`, and reported
`errors=[]`. Candidate and auditor exit codes were both 0.

| Policy | Complete/allow | Counterexample/reject | Partial unknown | Unsafe partial ALLOW |
|---|---:|---:|---:|---:|
| All-or-nothing timeout | 4 | 2 | 9 | 0 |
| Unsafe scalar progress control | 11 | 0 | 4 | 11 |
| Claim ladder | 4 | 2 | 9 | 0 |

All policies were descriptive-only: the audited consumer-authority field was
false and total consumer side effects were zero. “ALLOW” above is a simulated
verdict label only; it did not execute any action.

For the frozen source-current decisive identity-negative trace, claim-ladder
`COUNTEREXAMPLE` occurred at logical time 1 ms, while all-or-nothing waited for
all mandatory checks and returned at 11 ms. This is a 10 ms difference in the
stipulated logical cost model, **not** measured wall-clock latency or a real
verifier speedup. The claim ladder matched all-or-nothing on the overall
complete/reject/unknown counts in this small table; no general benefit rate is
claimed.

The partial-positive prefixes remained `PARTIAL_UNKNOWN` under the claim ladder.
Same-generation contradictory receipts, wrong-generation and wrong-claim
receipts remained UNKNOWN. The torn freshness receipt was excluded from
durable coverage, so the missing-mandatory row did not complete. In the modeled
crash-after-durable-receipt trace, recovery replayed the two durable receipts
and the complete verdict had a single modeled final commit. A duplicate-replay
trace recorded six replay applications (two replays of three durable receipts)
while the modeled final commit count remained one.

## Gate and construction evidence

Five preformal local harness tests passed. They covered partial-positive
abstention, early-negative logical ordering, same-generation contradiction,
torn/durable receipt boundaries, durable replay idempotency, 45-row independent
reconstruction, and four raw corruption mutations. These are construction
tests; they are not additional candidate invocations or empirical replicates.

The formal auditor independently checked policy×scenario cardinality, source
fixture digest, durable receipt reconstruction, disposition, logical decision
time, recovery replay count, final modeled commit cardinality, non-authority,
and zero side effects. Formal raw SHA-256:
`33cbba8b92fb14dc1182c498cde710ca497f0ec5f59ada3d7c5fca12f344af69`.
Audit SHA-256:
`eee58b569158c8c64aab14203d9e37c504d1cb32411caa8eaa5425063c306e81`.

## Environment and chronology

- Base source main: `8150aa7f55c490bc1f1cdd861c764ec27d2e3fb2`; latest main checked
  at the final gate: `cf467e076b67f103e50fbbd47cc43007624a2ca8`. The intervening
  change was in a separate #5960 evidence path and `research/analysis/README.md`;
  no governed source or this allocation path changed. This exact disjoint update
  was recorded in `FREEZE.json` and on Issue #6509.
- Candidate: 2026-10-02 04:43:10 UTC, exit 0; container
  `58fee4e89df13b37dd1d5f19945c8ef2558ac887a3be9d594e6025a8e54df1e1`.
- Auditor: 2026-10-02 04:43:12 UTC, exit 0; container
  `f7e4ed1a1f5828344bde2af134c9108bbee092628ba81c89e1ffded8b4f3d98a`.
- OrbStack Docker context, `linux/arm64`, pinned
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`;
  network disabled, CPU request 0.25, memory request 512 MiB (no host-enforcement
  claim), PIDs 32, read-only root/source, all Linux capabilities dropped, and
  no-new-privileges. Candidate raw mount was writable; auditor raw mount was
  read-only and audit output was separate.
- The pre-existing `unjuno-native-ci-6092` container was observed at 0.00% CPU
  in the immediate preflight and was not modified. Both experiment containers
  used `--rm` and are absent after completion.

The preparation freeze was updated twice before any formal invocation because
main advanced. Those earlier bases (`f6c6d2004` and `900c4836`) were explicitly
unexecuted; no candidate or auditor retry occurred. The final source/fixture
hashes are the ones in `FREEZE.json`.

## Scope limits

This is a finite, authored deterministic state-transition model. Check outcomes,
service costs, evidence generations, durability markers and deadline behavior
were stipulated by the fixture. It does **not** test an actual disk journal,
filesystem crash consistency, concurrent threads/processes, GUI state, model
behavior, real scheduler jitter, actual deadlines, verifier truth, safety,
authority, user benefit, or product performance. A complete verdict is not an
application-effect or authorization receipt. Any live/disposable GUI follow-on
is a separate allocation with a new preregistration and independent target/oracle.
