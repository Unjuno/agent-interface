# Issue #5265 — finite state-machine result

## Disposition

**`PASS_CROSS_PRODUCER_EFFECT_COALESCING_SCOPED` for the frozen synthetic T0 only.** The candidate reduced the identical same-state/two-producer case from 2 simulated effects to 1. It did not coalesce any frozen distinct-identity case. This does not close Issue #5265 and does not justify a runtime abstraction or promotion.

## Frozen run

- Allocation: `effect-coalescing-5265-main-70b69b47-20260930-01`.
- Base/main: `70b69b47845b35afde59c2a5f0b56c6f906c6904`.
- Candidate branch: `research/effect-coalescing-5265-70b69b47-20260930-01`.
- Formal invocation: exactly 1; exit 0 at 2026-09-30 09:00:52–09:00:53 UTC.
- Host: Ubuntu 24.04 / WSL2, CPython 3.12.3; standard library only. No Docker/container, network, model, GUI, GPU, or task input was used.
- Raw: 29,332 bytes, SHA-256 `a1fe2d136d9dadaee3ea9672b5156e6a3aac4eedb2df09a13586a7fb402296f9`.
- Independent audit: separate CPU process, exit 0, status `PASS_CROSS_PRODUCER_EFFECT_COALESCING_SCOPED`, errors `[]`, source errors `[]`.
- Audit: SHA-256 `024f766743e9478512d277b50ef5e567555ff5e52b58b08e849539ead3451dd3`.
- Corruption controls: 7/7 rejected (effect count, case order, target incarnation, preregistered expectation, authority claim, duplicate case, workload hash).
- Construction before freeze: 20/20 tests passed and no-write Python compilation passed. One malformed discovery invocation is preserved in `CONSTRUCTION.md`; no test method ran in that attempt.

## Per-case observed outcomes

| Frozen case | No-coalescing effects | Semantic coalescing effects | Candidate decisions |
|---|---:|---:|---|
| Equivalent cross-producer, same state | 2 | 1 | `EXECUTE`, `COALESCED` |
| Same coordinates, new target incarnation | 2 | 2 | `EXECUTE`, `EXECUTE` |
| Same effect, different expiry | 2 | 2 | `EXECUTE`, `EXECUTE` |
| New intent revision | 2 | 2 | `EXECUTE`, `EXECUTE` |
| Verified state/effect-opportunity transition | 2 | 2 | `EXECUTE`, `EXECUTE` |
| Late proposal already satisfied | 1 | 1 | `EXECUTE`, `NO_ACTION` |
| Same-producer retry | 1 | 1 | `EXECUTE`, `DEFER_TO_ISSUE_24` |
| Changed parameters | 2 | 2 | `EXECUTE`, `EXECUTE` |
| Missing target incarnation | 0 | 0 | `YIELD`, `YIELD` |
| Expired proposal | 0 | 0 | `YIELD_EXPIRED` |

The immutable raw contains both policies' complete decision rows and proposal/producer provenance. The independent oracle imports neither candidate simulator nor candidate identity helper.

## Limits / next decision

This is deterministic synthetic state-machine evidence only. It does not model actual concurrent admission, application feedback, effect observation delay, event loss, held-input/resource cleanup, or a real live action. It therefore does **not** establish release/cleanup correctness required by the broader Issue decision, exactly-once behavior for arbitrary GUIs, or that #24 idempotency plus #732 single-writer/resource ownership is insufficient. Keep #5265 open; any follow-up must be a distinct, preregistered composition/live rung, not a replay of this allocation.
