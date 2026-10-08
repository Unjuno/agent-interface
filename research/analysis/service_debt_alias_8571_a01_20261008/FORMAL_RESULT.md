# Issue #8571 A01 — formal result

Disposition: `PASS_METHOD_SCOPED` (not a claim about deployed systems).

## H / T / D / C / U

- **H:** Keying least-cumulative-service debt by caller-presented IDs can alter and advantage one principal's share when the same four requests are split into alias groups; fixture-trusted-parent grouping should restore the one-identity schedule.
- **T:** Frozen base `5215aab506f43c8a02470d495b7352b1326a9580`; deterministic Python 3.12.3 / native Ubuntu WSL; standard library only. Four eligible one-unit A requests and four B requests, four-slot horizon, all 15 set partitions, FIFO/presented-debt/trusted-parent-debt; separate controls for fragmentation, three genuine principals, revocation, missing joint grant, false parent link, and mandatory release. One candidate invocation produced 66 rows; one independent auditor invocation replayed all 66.
- **D:** `PASS_METHOD_SCOPED` requires zero independent replay errors and the preregistered existential alias discriminator, while all alias partitions are retained, trusted-parent allocation is invariant, controls hold, and construction-time mutation probes are rejected.
- **C:** A four-slot finite synthetic schedule is not a real waiting-time or quality estimate. FIFO remained caller-label invariant. Different service units, arrival/deadline patterns, queue policy, semantics, or identity trust could change the result.
- **U:** No live agent, GUI, user identity, consent, authority, external resource, network, or production scheduler was exercised. No identity collection or policy recommendation follows.

## Result

The one-identity baseline allocated 2 service units each to A and B. Under presented-ID debt, 10 of the 14 nontrivial partitions allocated 3 units to A and 1 to B; four partitions (`alias_p02_k2a`, `alias_p03_k2b`, `alias_p04_k2c`, `alias_p05_k2d`) remained 2/2. Thus the frozen fixture supports a representation-sensitive consideration-share effect, but not a universal advantage for every split.

Under trusted-parent debt, every one of the 15 partitions exactly reproduced the baseline trace and 2/2 service allocation. FIFO is label invariant in the independent replay. Fragmentation base and split both allocated 2/2. Three genuine principals each received one dispatch. Revoked A work was excluded (A=0, B=4); missing-joint-grant work was excluded; the false parent assertion was rejected; mandatory release occurred at tick 2 after two one-tick jobs, with no later work dispatched. Independent audit: 66 rows, zero errors.

Construction log: before freezing, an overstrong all-partitions-have-effect assertion failed. Fixed partition enumeration identified four nulls and ten effects. The decision gate was narrowed before freeze to an existential discriminator across the complete fixed set, retaining every case. A revoked-control assertion was also corrected to distinguish explicit zero-service A from absent A. These were construction failures, not formal runs; they are retained in `README.md`.

## Integrity and reproduction

Inputs and code hashes are in `FREEZE.json`. Output hashes:

```text
candidate_raw.json  dfbdb4c1decb3b065008faeb89e4a19dd314ed76fd49284db13e361e6551ce16
audit.json          ecc5dadc2dd8b8a8467d4c9f9ad3e8c7d4ca96b4c5d4c4f5489e5fa8eed9f0be
```

Do not rerun the formal allocation. `candidate_raw.json` and `audit.json` are immutable first-run outputs. The independent auditor was implemented separately and consumes candidate raw output plus the frozen outcome oracle; the candidate does not read the outcome oracle.

