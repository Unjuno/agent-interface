# W2 cross-clock lease authority boundary — 2026-09-28

## H / T / D / C / U

- **H:** W2 verifier and raw-trace auditor compare lease-open timestamps to input edge brackets using numeric nanoseconds without requiring a shared clock domain/epoch or retained calibration receipt. A validly declared but cross-domain lease can therefore be treated as authorizing input when the numeric values happen to order favorably.
- **T:** Freeze current-main runner, independent auditor, schema, and eight-case fixture; establish full-CLI baseline; mutate only the `release-before-terminal` case by moving lease-open event `r0` from `(mono,s4)` to a newly declared monotonic domain `(other,lease-epoch)`, leaving its timestamp 0 and the input edge on `(mono,s4)`; add no conversion/calibration receipt; run verifier CLI and independent audit CLI.
- **D:** The boundary is exposed if verifier does not HOLD the affected trace for incomparable clocks (specifically if it reports `unauthorized=false`) and independent audit reports no cross-clock integrity error. A HOLD is the required safe outcome under the contract.
- **C:** One deterministic synthetic fixture mutation; static/offline only. Does not demonstrate live unauthorized input or a production trace failure.
- **U:** No calibration-receipt schema exists in this fixture; no live backend, GUI, model, input, task-effect, recovery, or MAP01 evidence; no fix implemented; W3/W4 and Gate 1 remain untouched.

## Provenance and frozen current main

- Repository: `Unjuno/agent-interface`.
- Current-main SHA observed and independently compared with ref `main`: `eb3c8d108b8ddd090e5e81a22c7d5db9c367552c` (compare status `identical`).
- Runner `research/orchestration/o2_g1/w2_measurement_v2_20260927/verify_contract.py`: Git blob `d8f4221811b160e5714d2d6e4154c82af94d633e`; SHA-256 `6bf7c2c2fc4b221a51ddd8a615777ddf11617c4ece4a03465e3bbbbf3b724c35`.
- Independent auditor `.../audit_contract.py`: Git blob `1942546e60ad7e6cb56b9a383830033db14d0397`; SHA-256 `f00677e91ceb3a67bddff0d941e076649c8da759f422c3a193725b2e897eacb7`.
- Schema `.../event-schema.json`: Git blob `ebc424d2df631aa74c6d9aee4699c595a27ed589`; SHA-256 `3ca91926d9e362e02dd0272a03b67e2d65b46199bcfb1bb8f55c29cfe92f6d76`.
- Base fixture `.../trace-cases.json`: Git blob `0a49a00567c25766495cd332be50f6c2946781f7`; SHA-256 `6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f`.
- Host: Python 3.12.10; Docker Desktop Linux engine/context `desktop-linux`, client/server 28.5.1. No container was started: coordination Issue #5085 and active Issue #5074 explicitly retain the shared Docker slot through refreeze, one formal run, audit, and explicit release. An idle engine is not release evidence.
- All run artifacts were disposable files under the host temporary directory; no checked-out project/source/fixture was modified.

## Executed baseline and attempts

Baseline full verifier CLI: exit 0, stdout `PASS_MEASUREMENT_CONTRACT_CONSTRUCTION_SCOPED 8/8`; baseline full auditor CLI: exit 0, stdout `PASS_RAW_TRACE_AUDIT_SCOPED cases=8 numeric=5 mutations=7/7`. Baseline report hashes: verifier `1a7f8613d4252b1c7427ed311e5cec2ad478065cf4252a1cdc30d1ce22451c8c`; auditor `b3266592ef7cfc16860db769ac5a0f505c393865d7b9538af5807e60720b43cd`.

Attempt 1 deliberately retained as a construction STOP: moving `r0` to `(other,lease-epoch)` without adding that domain to the fixture caused the verifier to normalize and accept the domain, but the independent auditor stopped with `baseline traces fail invariants: ['unknown_clock']`. This was a malformed test fixture, not an experiment result.

Attempt 2 corrected only the fixture declaration by adding `{domain_id: other, epoch_id: lease-epoch, kind: monotonic, unit: ns}`; no clock-conversion receipt was added. Both full CLIs exited 0:
- Verifier stdout: `PASS_MEASUREMENT_CONTRACT_CONSTRUCTION_SCOPED 8/8`.
- Auditor stdout: `PASS_RAW_TRACE_AUDIT_SCOPED cases=8 numeric=5 mutations=7/7`.

Input/result SHA-256:
- Mutated trace: `2e9ebac0bf9efece38a223961cd1ac404bf67e7be27f2ac274f86dcf7c2d817b`.
- Verifier report: `1b5694ba68e056c66914695bf0603c223fde104b86377bf29ea1abe4842e46d7`.
- Auditor report: `48278dbbe8efe71baf4266d19d25bac75f762ecb6c7be65f1cf5917e8415e29e`.

## Raw result excerpts

Verifier row for the affected case:

```json
{
  "case_id": "release-before-terminal",
  "disposition": "COMPLETED_RELEASE_BEFORE_TERMINAL",
  "guaranteed_any_input_ns": 298,
  "ordered": true,
  "possible_any_input_ns": 302,
  "program_envelope_ns": 500,
  "task_effect": "UNRESOLVED",
  "terminal_does_not_extend_input": true,
  "unauthorized": false,
  "unmatched_down": false
}
```

Independent audit report:

```json
{
  "case_count": 8,
  "case_result_mismatches": [],
  "corruption_controls_rejected": 7,
  "disposition": "PASS_RAW_TRACE_AUDIT_SCOPED",
  "errors": [],
  "limits": [
    "audits only retained synthetic trace examples",
    "no live authority or efficacy claim"
  ],
  "mutation_names": [
    "duplicate_event_id",
    "unknown_clock",
    "inverted_interval",
    "task_effect_source",
    "edge_state_contradiction",
    "terminal_release_event_invalid",
    "unbound_effect_attributed"
  ],
  "naive_sum_ns": 76,
  "numeric_reconstructions": 5,
  "overlap_union_ns": 58,
  "schema": "o2-g1-w2-independent-audit-v2",
  "trace_sha256": "2e9ebac0bf9efece38a223961cd1ac404bf67e7be27f2ac274f86dcf7c2d817b",
  "verification_sha256": "1b5694ba68e056c66914695bf0603c223fde104b86377bf29ea1abe4842e46d7"
}
```

## Scoped disposition

**FAIL — incomparable lease-open and input-edge clocks are treated as directly comparable.** Contract v2 says timestamps may be compared only within the same monotonic clock domain and epoch; cross-domain comparison requires a retained conversion receipt with uncertainty. Here `r0` on `(other,lease-epoch)` opens at numeric 0, while input edges remain on `(mono,s4)`; without a receipt, the safe disposition is HOLD. The verifier instead reports an authorized completed-input trace and the raw auditor independently accepts it. This is distinct from #5101's parent-reference/causality counterexamples and is a synthetic contract-boundary defect, not proof of live misuse.

## Integration-ready acceptance criteria

A separately authorized additive repair should preserve all eight current baseline cases and enforce clock-domain compatibility before lease/edge comparison in both verifier and independent raw auditor. Same-domain comparisons remain valid; cross-domain comparisons without a retained conversion receipt must HOLD; with a receipt, propagate its uncertainty and test boundary values. Add paired tests for cross-domain lease-open and lease-close comparisons; the auditor must reconstruct the disposition from raw rows rather than trusting verifier output. No W2 implementation lease, runtime/formal allocation, W3/W4 activation, or live experiment is authorized by this report.
