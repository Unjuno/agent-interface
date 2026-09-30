# Issue #5315 — finite-sample conformal first unit

## Decision

**`PASS_FINITE_SAMPLE_UNIT_SCOPED`; Issue-level `HOLD_UNVERIFIED_FULL_RISK_CONTRACT`.** The single frozen simulation and corrected additive raw-only audit support the finite-sample boundary for the declared synthetic score laws. The deliberate shift lowered split-conformal inclusion below the 90% target. An oracle-supplied shift flag safely widened to the full set, but no shift detector, real task population, production verifier, or full Issue policy comparison was tested. Keep #5315 open.

## H / T / D / C / U

**H.** For the declared synthetic population, split-conformal rank selection must not emit a singleton when 90% marginal inclusion is unattainable at the calibration size; under exchangeability its true-label inclusion should satisfy the finite-sample order-statistic expectation. Reusing the calibration sample under a known score-distribution shift should break the nominal guarantee; an explicit `SHIFT_DETECTED` input should suppress singleton claims.

**T.** One no-model OrbStack simulation, frozen at main `537c84162074c7687480ccb8936b8d58c34d9a7d`, source commit `bf7707f2e1b1ece696d352960de510f12d56e184`, seed 5315, alpha 0.10, and 10,000 calibration/test replicates at each `n ∈ {4,10}`. Calibration and IID true/false scores are `sqrt(U)` with CDF `x²`; shifted true/false scores are `U^(1/4)` with CDF `x⁴`. Compared raw threshold 0.90, plug-in rank `ceil(n·0.9)`, split-conformal rank `ceil((n+1)·0.9)`, and an oracle-provided shift flag that returns the full binary outcome set. Exact commands, immutable input/code hashes, image identity, and limits are in [FREEZE.json](FREEZE.json), [COMMANDS.md](COMMANDS.md), and [AUDIT_V2_FREEZE.json](AUDIT_V2_FREEZE.json).

**D.** One formal container invocation generated 20,000 JSONL rows. Independent audit v1 exited 1 because one of its own mutation controls was a no-op; its output remains preserved unchanged. Additive audit v2 examined the exact same raw SHA-256 `4ead9d0a552db86332a4c8ac08b9f6e01fcc1f6066e645ae15ead9c9395c8b37`, reconstructed every row and the aggregate receipt, passed all finite-sample expectations within ±0.015, and detected all three mutation controls. It returned `PASS_FIRST_UNIT_SCOPED`.

For `n=4`, the conformal rank is 5 (>4), so the method returned both outcomes for every case: true-label inclusion 1.000, singleton rate 0, mean set size 2. For `n=10`, the IID conformal inclusion was 0.9025 against expectation 0.9091; plug-in was 0.8125 against 0.8182. Under the known shift, conformal inclusion fell to 0.8261 against 0.8333 (below the requested 0.90); plug-in was 0.6746 against 0.6818. The explicit shift-flag override returned the full set in every trial (singleton rate 0). Raw-threshold inclusion was 0.8053 IID and 0.6468 shifted at n=10. These are synthetic label-set inclusion rates, not real verifier error rates or task success.

**C.** These conclusions depend on the stipulated continuous score distributions and independent draws. The shifted condition is deliberately non-exchangeable relative to calibration. `SHIFT_DETECTED` is an externally supplied oracle flag, not a detector measured here. The false-label score law and set construction also influence singleton/error trade-offs.

**U.** This does not validate a representative task/domain population, adaptive queries, real verifier accuracy, temporal/UI/tool shift detection, calibration lineage/freshness, a deployed certificate checker, effect truth, authority, or product safety. It does not compare the full Issue matrix, including a deterministic fixed-checklist implementation. The earlier #1903 retained-evidence identifiability result remains unchanged and addresses a separate question.

## Preserved execution/audit sequence

1. Formal allocation 01 ran once in pinned OrbStack Python 3.12.14 Linux/arm64, no network, read-only root and source, 1 CPU / 512 MiB / 128 PIDs. Raw and receipt are immutable.
2. Audit attempt 01 failed only its mutation self-control (it assigned `true` to a field already `true`). The failure is preserved in `results/formal-01/audit.json`; it was not overwritten.
3. Auditor successor v2 was separately frozen and run once against the exact same raw and receipt. It passed; see `results/formal-01/audit-02.json`. No formal rerun, replacement, exclusion, or tuning occurred.

Construction tests passed 4/4 on the host and in the pinned container before the formal allocation. The Issue-level result remains HOLD; this unit is intended as one executed step for later independent integration/revalidation, not an implementation recommendation.
