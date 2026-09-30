# Issue #5315 — finite-sample conformal claim gate (first experimental unit)

## H / T / D / C / U

**H.** In a declared synthetic population, the split-conformal finite-sample rank gate must not emit a singleton when the requested miscoverage is unattainable from the calibration sample, and its nominal marginal coverage should hold under exchangeability. Reusing the same frozen calibration set under a deliberate score-distribution shift should invalidate the nominal guarantee; an explicit externally supplied shift flag must suppress singleton claims. This tests one mathematical/statistical boundary only, not a useful production certificate.

**T.** One deterministic, no-model Python simulation in OrbStack. For each calibration size `n in {4, 10}`, run 10,000 independent replicates with `alpha=0.10`, seed `5315`, calibration nonconformity scores `sqrt(U)` for iid `U~Uniform(0,1)` (CDF `F(x)=x^2`), and one independent in-distribution test plus one shifted test per calibration set. Shifted true-label scores and false-label scores are `U^(1/4)` (CDF `F(x)=x^4`). Compare: (1) fixed raw threshold `0.90`; (2) plug-in empirical rank `ceil(n*(1-alpha))`; (3) split-conformal rank `ceil((n+1)*(1-alpha))`; (4) the contract response when a known `SHIFT_DETECTED` input is present. A rank above `n` means full outcome set / no singleton, not a clipped finite threshold. Form a prediction set from true- and false-label scores; count true-label inclusion, singleton claims, wrong singleton claims, set size and empty sets. Keep the source read-only in the container and write raw JSONL plus receipt only to a fresh output mount. No network, model, provider, GUI, GPU, runtime integration, or user data.

**D.** PASS this narrow unit only if the independent raw-only auditor reconstructs every decision and all aggregates, no rank-above-`n` arm emits singleton, exact finite-sample oracle expectations are within preregistered Monte Carlo tolerance `0.015`, and the known-shift policy emits no singleton. Expected marginal true-label inclusion: raw threshold ID `0.90^2=0.81`, shifted `0.90^4=0.6561`; for a finite order rank `k` on `n` calibration observations, plug-in ID inclusion is `k/(n+1)` and shifted inclusion is `k(k+1)/((n+1)(n+2))`; split-conformal uses `k=ceil((n+1)*0.9)`. When that rank exceeds `n`, output the full two-outcome set, giving inclusion 1, set size 2, and zero singleton claims. HOLD the Issue overall: this first unit cannot validate a shift detector, representative task population, risk calibration for real verifiers, or causal effects.

**C.** The result depends on the synthetic score family and known shift, not a fitted production model. Finite Monte Carlo error, ties (probability zero for these continuous draws), and the chosen false-label score distribution can affect observed rates. In particular, supplying the shift flag is an oracle control, not a tested detector.

**U.** No empirical claim about actual agent traces, exchangeability units, adaptive query streams, UI/tool versions, certificate schema, freshness/lineage, verifier accuracy, external effects, authority, or product safety. The related #1903 retained-data identifiability audit remains distinct and unchanged.

## Frozen allocation

- Allocation: `conformal-risk-5315-v01-20260930-01`
- Main base: `537c84162074c7687480ccb8936b8d58c34d9a7d`
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Runtime: OrbStack Docker Engine 29.4.0, Linux/arm64; network disabled; read-only root and source; 1 CPU, 512 MiB memory, 128 PIDs.
- One formal invocation; no retries, replacements, tuning or exclusions.

Exact code and input hashes are in `FREEZE.json`; executed command and outputs are in `COMMANDS.md` and `results/formal-01/`.
