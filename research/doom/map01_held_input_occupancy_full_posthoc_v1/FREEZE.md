# Pre-compute freeze — full retained MAP01 held-input occupancy posthoc

Task: `MAP01-HELD-OCCUPANCY-FULL-POSTHOC-20260916-001`; Issue #428.
Immutable publication BASE: `9558313ed704804031733031f9e9443ddffc54de`.
No retained-log computation has run at publication of this freeze.

## Frozen source identities

- existing interval analyzer Git blob: `4ac4180f8768b3c94f2da5d0e0abcf20de2d69ca`
- existing analyzer regression test Git blob: `6fd9713dbcfc449296d6dcba0b63062ea32bb28a`
- new runner Git blob: `a6b5cd3f66a2a558aefd40659965ec5c8ecbca04`
- new runner SHA-256: `34d23b2a6f724de86768d1ae3a48fd6f608761b2ef5a4c077ab4cd3a1d7df18a`
- independent auditor Git blob: `f5c9e934aa49c8cea53d09475cfa63fe73b50860`
- independent auditor SHA-256: `f4a6aedee3fce68835728e45d03943bb9dae787cde5f7a8099447069eb8614a4`

GitHub readback matched the local runner/auditor Git blob identities exactly before this freeze.

## Frozen retained inputs

| retained run | report.json SHA-256 | runtime/events.jsonl SHA-256 |
|---|---|---|
| `map01-v38-integrated-threat-live-01` | `7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58` | `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3` |
| `map01-v39-coast-liveness-live-01` | `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687` | `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381` |

These identities come from already-retained analysis/evidence. Any mismatch stops the computation; no source substitution is permitted.

## Frozen measurement semantics

Reuse `analyze_map01_held_input_occupancy_v1.py` exactly. Normal key-up timestamps are absent, so physical any-key occupancy is interval-censored. Never substitute programmed hold duration or accepted-to-terminal program envelope for physical occupancy. Every hold must retain `exact_physical_duration_known=false`.

For each retained decision, intersect the conservative hold lower/upper interval with the retained model-wait window. Aggregate the per-decision physical occupancy lower bound, upper bound, and interval width.

## Frozen diagnostic disposition

For **both** retained runs, call the interval metric informative enough for a later matched experiment only if:

1. aggregate interval width / total model-wait `<= 0.10`; and
2. aggregate interval width / aggregate occupancy upper bound `<= 0.25`.

If both runs satisfy both gates: `RETAIN_FULL_OCCUPANCY_INTERVALS_SCOPED`.
If integrity passes but either run misses either gate: `SCHEMA_CENSORING_TOO_WIDE`.
Any source/order/arithmetic contradiction: `FAIL_INTEGRITY`.

These thresholds are finite diagnostic gates, not a reliability, gameplay, safety, or production metric.

## Compute boundary

One branch-only GitHub Actions workflow may checkout this exact branch and execute the frozen existing regression test, runner, and auditor against GitHub-retained bytes. It performs no model/provider/GUI/XTEST/game calls. It must be removed before the result PR; final merge scope remains this research directory only. No retry or method change after the first completed computation.
