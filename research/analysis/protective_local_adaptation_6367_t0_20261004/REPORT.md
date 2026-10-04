# Issue #6367 T0 — all-offer matched protective-adaptation method test

## H / T / D / C / U

**H.** For a finite externally scheduled challenge stream, an all-offer paired
policy-assignment ledger distinguishes a planted useful/safe adaptation
contrast from null and adversarial controls without treating a selected
“adapted and successful” subset as causal benefit.

**T.** Nine matched A/B pairs (18 offers), one deterministic challenge schedule
per pair, fixed effect/release receipts, a raw-only auditor, and three
mutations: hide one externally scheduled offer; mutate generation in a benefit
case; alter a release/effect receipt. Controls include benefit, null, suppressed
action, late response, stale generation, missing occupancy, safety violation,
and a selection trap. See `fixture.json` and `events.json`.

**D.** Formal candidate and audit outcomes are in `out/`; total test status and
exact counts are in `RESULT.json`. `FREEZE.json` records the exact main/source
identities and formal invocation caps. Construction repair history is preserved
in `CONSTRUCTION.md`.

**C.** `METHOD_PASS_SCOPED` requires exact all-offer reconstruction, correct
case classifications, no benefit credit for null/suppression/late/stale/missing
controls, `FAIL_SAFETY` on a successful-but-unsafe case, and detection of all
three auditor mutations. The result is only method conformance on this authored
finite fixture.

**U.** No live #59 efficacy, MAP01 survival/progress, exact physical occupancy,
human-tempo, model-cost, or product claim. The T0 does not implement the next
live UNKNOWN-recovery mechanism and does not satisfy Issue #59. Latest #59
evidence at intake is PR #7577's `HOLD_COMPARATIVE_VALUE` after a guarded arm
aborted on typed health/ammo UNKNOWN; its first result remains unchanged.

## Execution protocol

- Allocation: `PROTECTIVE-ADAPTATION-6367-T0-20261004-01`.
- Main lineage: intake `8a462fa02d01801b166a4ae00edaa41a6f29eb67`, then
  `5ce152e1479bedac08f55db45d24b3dd1405cb16`, then latest pre-freeze main
  recorded in `FREEZE.json`.
- Branch/path: `research/6367-protective-local-adaptation-t0-20261004` /
  `research/analysis/protective_local_adaptation_6367_t0_20261004/`.
- Formal commands (after freeze and preflight):
  `python3 candidate.py fixture.json events.json out/CANDIDATE.json`;
  then only on exit 0, `python3 auditor.py fixture.json events.json out/CANDIDATE.json out/AUDIT.json`.
- Candidate max 1, independent audit max 1, retries 0. Unit/preflight test
  invocations are construction, not formal fixture runs.
- OrbStack exact-image inspection/list fails with a containerd content-blob
  `operation not supported`; no pull/retry or container launch. This CPU-only,
  no-GUI/no-model test uses the registered host-Python fallback.
