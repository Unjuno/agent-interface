# Frozen source and decision gate

- Issue: [#6155](https://github.com/Unjuno/agent-interface/issues/6155)
- Successor allocation: `MULTIFIDELITY-ROUTE-CONTRAST-6155-T0-20261002-01`
- Base `main`: `39cff8c45e3df04f1f7e98962b043c3fb0179ed2`
- Branch: `research/6155-route-contrast-covariance-20261002`
- Package: `research/analysis/multifidelity_route_contrast_6155_t0_v1/`
- Image: `python:3.12-slim`, linux/arm64, cached RepoDigest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Formal source freeze created before candidate invocation. No formal command has run.

## Frozen inputs

| File | SHA-256 |
|---|---|
| `PLAN.md` | `a71098c2a3ce07c1ff625fd4fc1d64f923b4d05c11d1fda6b8c91cd527cd16a8` |
| `candidate.py` | `96f140d58191a97fa28a3e2a63065d9c4a3b7eecf763c4bbd9f4ed79bb61f8c1` |
| `audit.py` | `bd2355e6cf2082ed172522ab9553c88e622b52ca49b26da99e5ea61867995858` |
| `test_method.py` | `beff00d04f7887c8180a941d84ae13e15146a58eca8241ef85775dc21a8285be` |

`test_method.py` is construction-only and not an input to the formal candidate/auditor decision.

## Formal allocation and run order

- Cases: `shared_level_only`, `delta_positive`, `delta_negative`.
- Amortization grid: `K={1,5,20}`; 300 independent deterministic blocks per case/K; 2,700 raw block records total.
- Each block: 64 independent paired pilot rows; per scored cohort 20 paired `(ΔY,ΔX)` rows plus 80 independent same-population X-only rows; a Y-only comparator sized to the *entire* pilot+scored budget, plus 64 ignored low-fidelity units to balance the exact cost.
- Costs: one paired high/low unit=101, one low-only unit=1, one high-fidelity-only unit=100. Per block and arm total budget is exactly `6464 + 2100*K` units (K=1: 8,564; K=5: 16,964; K=20: 48,464).
- Candidate: one invocation, network disabled, CPU only, retries=0. Raw JSONL output is immutable after completion.
- Auditor: only after candidate exit 0, one separate network-disabled container; read-only candidate/raw mount; auditor independently validates raw identities, arm-minus-baseline arithmetic, row sets, the complete pilot-inclusive cost match, and reconstructs beta, estimators, MSEs, and Bonferroni family-wise 95% Monte Carlo intervals across all nine case/K cells. No candidate summary is trusted.

## Frozen decision gate

`PASS_METHOD_SCOPED` requires all 2,700 rows and 9 groups to be reconstructed with exact per-block cost equality and no raw errors; the shared-level negative control at K=20 must show mean level correlation ≥0.95, absolute mean difference correlation ≤0.10, absolute mean pilot beta ≤0.10, and no Bonferroni-family-wise-resolved CV MSE improvement. Both signed predictive controls at K=20 must show absolute mean difference correlation ≥0.70, at least 5% MSE reduction, and a Bonferroni family-wise 95% interval for `(MSE_CV−MSE_Y-only)` wholly below zero. Any violated gate is `FAIL_METHOD_GATE`; preserve arm-level outcomes and do not retry or tune.

## Start gate and current disposition

Latest pre-run check found OrbStack context `orbstack`, exact image digest/platform cached, and unrelated running container `unjuno-native-ci-6092`. The other previously listed container is no longer running. No existing container was inspected beyond inventory, stopped, removed, or modified. The user explicitly requires a Docker/OrbStack experiment; this allocation uses a new uniquely named, CPU/memory-bounded, network-disabled one-shot container and its own output path, without interacting with the running container. This is not a claim that #5085 granted a shared slot. Candidate=0, auditor=0 at freeze time.
