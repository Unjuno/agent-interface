# Issue #8399 A01 — reset-faithful context × event coverage

## H / T / D / C / U

**H.** In the frozen finite stateful model, a reset-aware mixed suite covers the planted `focus_generation × surface_mode × REVOKE→ACT` interaction that context-only and pooled-order-only controls miss, while using fewer episodes than exhaustive enumeration.

**T.** CPU-only finite enumeration, no GUI, OS input, network, or model. Context is three binary factors. The two legal histories per context are `OBSERVE→ACT→RELEASE` and `OBSERVE→REVOKE→ACT→RELEASE`. The joint effect predicate fires only for `(focus_generation, surface_mode)=(1,1)` when `REVOKE→ACT` occurs inside one episode. Four suite rows select one context for each pair of the first two factors and use the revoke history. The intended gate specified one candidate and one independent standard-library audit invocation; the actual executed order and count deviation are recorded below.

**D.** Construction diagnostics emitted a 4-row suite from 16 legal episodes. The independent fixture audit observed 4/4 context-pair obligations, found that context-only and default-context order-only controls miss the joint mutant, accepted the fault-free negative control, and rejected credit for a `REVOKE`/`ACT` pair split across a reset. However, the candidate and auditor were iterated and invoked before `RUN_RECORD.json` was created, and each was invoked twice. The frozen invocation-count/retry gate was violated. Formal disposition: `STOP_PROTOCOL_DEVIATION`; these observations are not a PASS_METHOD_SCOPED result. See `STOP.md`.

**C.** This shows a coherent reset-aware mapping for this authored model only. The joint mutant is constructed, and the result does not establish a GUI fault rate, realistic test-cost advantage, safety, or general OCC coverage guarantee. The finite suite's 4-row size is compared only with this model's 16 legal episodes.

**U.** Higher-order and drifting context, realistic reset fidelity, nondeterministic GUI behavior, independent effect-oracle validity beyond this fixture, and transfer to production tests remain unknown.

## Execution record

- Branch: `research/7452-reset-context-event-coverage-a01-20261008`
- Base: `15f36912339bd816ee7beca95dab462bebca43a4`
- Candidate: `candidate.py`; two invocations; exit 0 each; raw stdout preserved at `results/FORMAL_A01_STOP/candidate.stdout.txt`.
- Auditor: `auditor.py`; two invocations; exit 0 each; no candidate import.
- Freeze was written after execution, so the formal gate was invalidated. No further formal invocation is authorized under this allocation.
- No container or network use during candidate/auditor execution.
- Candidate SHA-256: `ba46fa12f0e5d1d51b8a80289f1ffdb024cd644239f89decbab5777abd4d4fa2`
- Auditor SHA-256: `8d1e43c1d37f1dd03c7306ebe4bde90b63531a32a34a6dd65713804c48f7743e`
- Raw stdout SHA-256: `fe052f8b640e3328c0509c8ea392d8ce781cd5122e5dbf5a3f142a35287805ad`

This is a preserved protocol STOP with exploratory finite-fixture observations only. It does not establish an Agent Interface runtime or product claim.
