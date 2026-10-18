# Issue #7709 T0 — synthetic coverage qualification

Status: pre-execution construction. This is a finite synthetic method test, not a route-performance result.

## H / T / D / C / U

**H.** With multiple independent sessions, session-level route-slope variation and within-session temporal dependence, a conventional attempt-i.i.d. interval will undercover the all-window paired route-latency contrast more often than a frozen segment-aware report that preserves detected temporal strata and uses sessions as the replication unit. Its integrated estimate must remain invariant to missed/extra segment boundaries and must retain censored windows.

**T.** Freeze `CONFIG.json`, `generate.py`, `candidate.py`, `audit.py`, this protocol, the image/runtime choice, and thresholds before generating held-out data. Generate a fixed-seed 4-family × 2-session-count × 500-replicate set with 24 ordered windows per session. Families cover stationary null, abrupt-shift null, warm-up null, and gradual-drift nonzero route effect. Every family includes AR(1) temporal dependence, independent session intercepts/slopes, and 10% administratively censored paired windows at 2500 ms; the all-window target includes these cap observations. A deterministic bounded split rule reports temporal regimes. Compare nominal 95% attempt-i.i.d. intervals against session-cluster intervals formed from the segment-weighted all-window contrast. An independent raw-only auditor reconstructs coverage, false promotions, widths, row accounting, boundaries, and boundary perturbations. No model, GPU, GUI, live app/input, formal allocation, WSLc, or Docker is used; the Issue explicitly permits this CPU-only T0 without WSLc when it avoids contention.

**D.** `PASS_METHOD_SCOPED` requires exact independent reconstruction of all 1,152,000 paired windows; every censored row remains in the all-window denominator; the segment-weighted estimate/interval is invariant within `1e-9` under no-boundary and extra-boundary partitions; three planted bad-result controls are rejected; the session-cluster interval has empirical 95% coverage in [0.90, 0.99] in every cell; and null false promotion is at most 0.10 in every null cell. The directional H gate is separate: pooled attempt-i.i.d. coverage must be at least 0.05 worse than session-cluster coverage in at least two nonstationary cells to support H. Unmet criteria are not rounded into PASS.

**C.** This synthetic DGP deliberately has independent sessions, a stable paired-route assignment, an additive session route slope, shared regime movement, Gaussian AR(1) noise, and independent administrative censoring. Real service queues, assignment/order effects, provider changes, informative censoring, treatment-induced task state, and segment-identification uncertainty may violate these assumptions. The fixed segmentation rule is a descriptive stratifier, not a causal change-point detector.

**U.** No real route latency, GUI/model behavior, route benefit, causal regime attribution, runtime change detector, correctness, safety, human tempo, or general performance claim. Synthetic coverage cannot retroactively alter historical results or authorize T1/T2.

## Frozen estimand and method

For each paired window, `d = route_B_ms - route_A_ms`; positive values mean B is slower. The all-window population estimand is the expected paired difference after the declared cap treatment, including every administratively censored window at 2500 ms. In this DGP the known truth is `beta_ms × (1 − censor_probability)`, because both arms are jointly capped and otherwise the additive route effect is beta.

The conventional interval treats all session-window paired differences as independent. The segment-aware analysis detects at most three boundaries from the pooled paired midpoint using the frozen 90 ms split threshold and four-window minimum segment length; it reports each temporal stratum, weights strata by their original window counts, and forms its nominal interval from independent session-level integrated contrasts. It retains warm-up, shifts, drift, timeouts, and all other windows in the all-window endpoint. It does not select the most favorable segment.

## Invocation ledger

Construction may include syntax checks only before freeze. After the freeze receipt is complete: run `generate.py` once to create held-out `INPUT.jsonl`; run `candidate.py` once; then run `audit.py` once. No retries or replacement allocation. Preserve any terminal STOP/FAIL output verbatim.
