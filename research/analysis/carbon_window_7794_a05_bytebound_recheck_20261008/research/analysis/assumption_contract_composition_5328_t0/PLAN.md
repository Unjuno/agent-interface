# Assumption-aware contract composition T0

Allocation: `assumption-contract-composition-5328-t0-20260930-01`
Issue: [#5328](https://github.com/Unjuno/agent-interface/issues/5328)
Registration main: `e034622e4307b1d2cb2d5e7cbb30211dcea661a9`
Frozen source main: `a1d0d0290b8619902d34b13d9e536c4bde063f74`
Branch: `research/assumption-contract-composition-5328-t0-20260930`
Path: `research/analysis/assumption_contract_composition_5328_t0/`

## H/T/D/C/U

**H.** Discharging explicit versioned assumptions prevents locally green observer/verifier/broker contracts from composing to PASS when environmental stability, capability, protocol, or evidence assumptions are false or unknown; compatible fully discharged contracts still compose.

**T.** Seven finite chain cases: compatible baseline; false backend stability; expired capability; protocol mismatch; missing assumption evidence; stale verifier digest; false component guarantee. Compare flat local-guarantee status with assumption-aware composition.

**D.** PASS_SCOPED iff baseline composes PASS; all false/stale/incompatible/missing assumptions yield UNKNOWN/STOP, never PASS; false guarantee yields STOP; five locally-green/local-only discrepancies are counted; all rows match a separate literal oracle; no authority/effect is emitted.

**C.** Host-only finite replay, Python 3.14.5 / Darwin arm64 / stdlib. No Docker/OrbStack CLI under #5085 coordinator hold. Runner and raw-only auditor each once; no retry.

**U.** Toy contract relation only; no proof of arbitrary implementations, assumption calibration, external system correctness, authority, or task success.
