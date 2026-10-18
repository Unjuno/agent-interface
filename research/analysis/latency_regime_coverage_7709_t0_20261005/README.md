# Issue #7709 T0 — coverage across non-steady trial regimes

## H / T / D / C / U

**H.** For a fixed all-window route-latency contrast with repeated time-ordered trials, a pooled row-level interval can undercover when trials are autocorrelated and nested in independently prepared sessions; a predeclared time-block summary with session-level inference should better calibrate uncertainty without dropping startup, shifted, drifted, or censored attempts.

**T.** One deterministic finite simulation: three workloads (stationary, abrupt shift, gradual drift), 240 Monte Carlo datasets per workload, eight independent sessions per dataset, 40 paired route attempts per session, four frozen 10-attempt temporal blocks. Both routes share the regime path and have true mean paired effect zero. A censored attempt remains in the all-window endpoint at its frozen deadline penalty. Compare conventional row-independent 95% intervals with a session-cluster t interval formed by weighting all four fixed-block means. Candidate and raw-only auditor each run once.

**D.** `METHOD_PASS_SCOPED` requires exact row/denominator reconstruction, the session-cluster interval to attain at least 90% empirical coverage in each workload, false route promotion at most 10%, and at least a 10 percentage-point coverage advantage over pooled inference in both nonstationary workloads. The fixed block map must be exact; missed/extra-boundary mutations must fail closed. All-window estimates retain every censored attempt.

**C.** Synthetic normal noise, a fixed number of sessions, a known fixed block width, and simulated pairing do not establish a suitable segmentation method or experimental unit for actual agent-interface trials. A different effect/censoring dependence can change coverage.

**U.** Finite synthetic calibration only. No Agent Interface route latency, model/provider, GUI, task correctness, safety, or performance benefit was measured. No previous result is regraded and no live allocation is authorized.

## Execution record

Issue #7709 specifies CPU-only finite simulation and says Docker/WSLc is not required. OrbStack inventory inspection also failed before container start with a cached containerd blob read error. The candidate was therefore executed once with host CPython; no image was pulled and no container was started. Exact counts, generator identity, raw ledger digest, and audit are in `FREEZE.json`, `RUN.md`, `RESULT.json`, `AUDIT.json`, and `SHA256SUMS`.
