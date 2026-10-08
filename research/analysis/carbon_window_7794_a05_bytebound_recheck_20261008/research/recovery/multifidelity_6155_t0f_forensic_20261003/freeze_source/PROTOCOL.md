# #6155 T0f — anytime stopping and current-row coefficient leakage

Status: preregistered finite synthetic method experiment. This does not revise the v1 unequal-cost observation, v2 cost-matched FAIL, v3 pilot-amortization point sweep, v4 independent-seed uncertainty result, or T0e route-contrast FAIL.

## H / T / D / C / U

**H.** Repeatedly inspecting ordinary two-sided 95% fixed-sample intervals can cross a one-sided positive-effect boundary too often under a planted null, while a bounded Hoeffding confidence sequence with a summable error allocation controls the false-stop rate. Re-estimating a control-variate coefficient from each same-row high-fidelity outcome can erase a real target mean and is not a valid predictable correction.

**T.** One deterministic, standard-library-only host-CPU simulation. Two strata, each with 10,000 independent streams of 1,024 observations: null `delta=0` and positive effect `delta=0.15`. For each observation draw independent `X, epsilon` from `{-0.25,+0.25}` with equal probability; `Y=delta+X+epsilon`. The target is `E[Y]=delta`; `E[X]=0`. The valid arm uses the prospectively fixed coefficient `beta=1`, giving `Z=Y-X=delta+epsilon` in the frozen bound `[-0.5,+0.5]`. At looks `{8,16,32,64,128,256,512,1024}`, compare (a) a repeated ordinary two-sided 95% normal interval and (b) a two-sided Hoeffding confidence sequence with `alpha_t=0.05/(t(t+1))` at every integer time `t`. The sum of all `alpha_t` is 0.05; the looks are a subset. As a deliberately invalid leakage control, compute `beta_i=Y_i/X_i` using the current row and `Z_i^leak=Y_i-beta_i X_i`; retain its estimate and show whether it erases the positive target. It is diagnostic only, not eligible for inferential promotion.

Seed: `615520261003`. RNG: CPython `random.Random`, seeded per (case,stream) with `seed + case_index*1_000_003 + stream`. Candidate emits exactly one JSONL row per assigned stream before audit. Candidate invocation=1; independent auditor invocation=1 only if candidate exits 0 and raw is complete; retries/replacements/tuning=0. No model/provider, GUI, input, network, WSLc, Docker/OrbStack, or GPU.

**D.** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs every stream exactly; under null, repeated-interval false stops exceed 0.05 by at least 0.02 while confidence-sequence false stops are at most 0.06; under `delta=0.15`, the valid fixed-beta CS detects at least 80% by `t=1024`; and the same-row leakage control returns estimates within `1e-12` of zero and detects at most 1% of the positive-effect streams. Otherwise retain the measured outcome as `FAIL_METHOD_GATE` or `HOLD_AUDIT` without tuning or rerun. The finite Monte Carlo result is not an arbitrary-distribution theorem; the Hoeffding guarantee follows only for the frozen bounded i.i.d. process and frozen filtration.

**C.** A valid independent pilot or fixed coefficient may be materially better than the intentionally pathological per-row leakage control; real task streams may be dependent, nonstationary, censored, or have an invalid bound. A simpler fixed-allocation design may be preferable to online stopping.

**U.** Synthetic arithmetic only: no actual GUI/model cost, population exchangeability, safety, correctness, confidence calibration under real task drift, or route-selection claim. No outcome can replace high-fidelity scoring or a hard safety gate.

## Exact allocation / freeze

- Allocation: `MULTIFIDELITY-6155-T0F-ANYTIME-CPU-20261003-01`
- Owner: this Codex task; bounded host-CPU process, no shared container/GPU/WSLc lane.
- Frozen main: `024ba046557b85d6921f114f65b5d18a79841843`.
- Branch: `research/6155-t0f-anytime-validity-20261003`
- Output: `research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/raw/`
- Source package hashes and exact source commit are recorded in `FREEZE.json` after staging and before the formal candidate invocation.
- Stop immediately if branch/source readback differs, current main changes the relevant issue/protocol/source/gate, output already exists, or another #6155 T0f allocation/branch appears. Preserve STOP and do not retry.

