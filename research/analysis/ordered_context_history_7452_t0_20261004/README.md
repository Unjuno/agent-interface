# Issue #7452 T0 — ordered event tuples crossed with context pairs

Status: `PASS_METHOD_SCOPED` on 2026-10-04. Candidate and independent raw-only auditor each ran once in native Ubuntu WSL2; retries 0. See [`RESULT.md`](RESULT.md) and [`FREEZE.md`](FREEZE.md).

## H / T / D / C / U (frozen before formal run)

- **H:** For this finite reset-separated stateful fixture, mixed coverage of each binary `(focus generation, surface mode)` assignment crossed with each feasible ordered length-2 event request will expose a seeded `focus=1 ∧ surface=1 ∧ REVOKE→ACT` fault that a separately satisfied context-pairwise suite and event-pair suite miss. At equal 40-row budget, mixed coverage should detect at least as many declared controls as the separate suite, with fewer rows than exhaustive context×event-pair enumeration.
- **T:** Three binary context factors `(focus generation, surface mode, evidence freshness)`; event requests `OBSERVE, REVOKE, ACT, RELEASE`; each row is a reset episode. A `RELEASE` request is legal only after `ACT`, with at most one release and no `ACT` after release. Context-only suite is the frozen four-row strength-2 binary array with `OBSERVE→OBSERVE`; event-only suite covers every feasible ordered pair at `(0,0,1)`. The equal-budget separate comparator adds distinct fixed-context legal triples to reach 40 rows without crossing the target context pair with `REVOKE→ACT`. Mixed OCC crosses all four `(focus,surface)` value pairs with each independently enumerated feasible event pair at freshness `0`. Exhaustive denominator is all eight full contexts crossed with every feasible pair. No model, GUI, input, GPU, network, or external service.
- **D:** `PASS_METHOD_SCOPED` only if the independent raw-only oracle confirms the exact mixed denominator, independent legality/reset rules, 40/40 equal budgets, 80 exhaustive rows, the joint fault is detected only by mixed coverage, factor/order controls are detected by the separate baseline, the order-invariant control is detected by both, and universe/stratum/impossible-history mutations are rejected. Otherwise `FAIL_NO_TRANSFER_VALUE` for semantically invalid or non-discriminating coverage; `HOLD_ORACLE_OR_RESET` if independent legal-history/reset semantics cannot be established. Do not interpret this synthetic method result as a GUI safety or reliability certificate.
- **C:** The seeded joint mutant may be contrived; a full event-history enumerator can be smaller for tiny fixtures; row-construction count is not execution cost; the freshness factor is deliberately outside the mixed strength; the model treats attempted `ACT` as an event even after revocation so that `REVOKE→ACT` is a legal observed request history whose stale admission is the seeded fault.
- **U:** One authored 3-factor/4-event finite model, one selected context-factor pair and length-2 tuples. No higher-order certificate, real GUI reset validity, safety, reliability, live failure rate, or universal coverage algorithm claim.

## Prior evidence and distinction

- #6206 / merged PR #6598: 33/33 feasible adjacent event pairs were covered in a finite sequence-only T0; frozen-auditor denominator caveat is retained. The #7452 experiment adds context-stratified ordered tuples; it does not rerun or amend #6206.
- #6262 / PRs #6289 and #6349: finite applicability-cell/pairwise certificates and an explicit higher-order unknown; it does not test the context-pair × within-episode event-order cross product. This experiment does not reuse its result as an oracle.
- NIST SP 800-142 and NIST CSWP 26 are established combinatorial/ordered-combination prior art. This is a repository-specific transfer check, not algorithmic novelty.

## Construction failure (preserved)

The initial construction test had 4 passes and 1 failure: `row-4-duplicate`, because the event-only `OBSERVE→OBSERVE` row collided with a context-only row. See [`CONSTRUCTION_HISTORY.md`](CONSTRUCTION_HISTORY.md). No formal candidate/auditor invocation occurred during that attempt. The event-only rows were moved to the distinct reset stratum `(0,0,1)`; the repair and later test result will be recorded separately.

## Formal result

The independent auditor reconstructed all 10 legal ordered pairs, the full 4×10 mixed denominator, and the 8×10 exhaustive reference. Mixed OCC and the separately satisfied factor/sequence baseline each used 40 rows; mixed detected the seeded joint mutant while the separate baseline did not. Both suites detected factor-only, order-only, and order-invariant controls. Corrupted context strata, an impossible release-before-action history, and dropped target-order rows were rejected by frozen construction controls. The audit ignored candidate-supplied expected-denominator metadata and reconstructed its universe independently. Exact outputs, hashes and limits are in `RESULT.md`.
