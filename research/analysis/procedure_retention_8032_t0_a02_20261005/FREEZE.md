# Issue #8032 ordinal-score power sensitivity — T0 A02 freeze

Allocation: `ISSUE-8032-T0-A02-ORDINAL-POWER-20261005-01`  
Base main: `7a9398add78d9095e5a85a60d324513fc3c2a1e3`

## H / T / D / C / U

- **H:** At the same score-scale standardized mean difference, different five-category ordinal baseline shapes can change the per-contrast completer count required for 80% marginal power. Therefore A01's two-independent-means approximation is an assumption check, not an ordinal-outcome sample-size answer.
- **T:** Simulate two independent samples on the A01 ordered step-score scale `{0,.25,.5,.75,1}`. Three authored PMFs (middle, ceiling, floor-skew) are each shifted under a common cumulative proportional-odds model to score-scale `d=.35` and `.50`. Compare with a two-sided tie-corrected normal-approximation Wilcoxon rank-sum test at Bonferroni alpha `.0125` for each of four co-primary contrasts. Frozen completer grid: 60, 80, 100, 120, 150, 180, 220, 260, 320 per arm; 2,400 independent synthetic cohorts per cell; one 20,000-replicate null calibration at n=120/arm. A seeded SplitMix64 generator and categorical inverse-CDF sampling make cells reproducible. See `protocol.json` for complete settings and limitations.
- **D:** `PASS_METHOD_SCOPED` requires the separate auditor to reproduce all cell rejection counts and pooled-category trace digests, verify effect calibration/PMFs/source hashes, and validate the null-control Wilson interval contains `.0125`. A grid n is only “at target” when its simulated power's Wilson 95% lower bound is at least `.80`. The coarse grid does not establish exact minimum N. If no grid value qualifies, disposition is range-limited HOLD, not infeasibility.
- **C:** The answer is scenario-dependent because the score PMFs and proportional-odds shift are authored. A simpler mean-based test, baseline adjustment, or different primary score might change power. Manual/retrieval arms could have different effects; this sensitivity assumes the same marginal `d` for each contrast.
- **U:** No participant or pilot data; no smallest meaningful effect; no joint four-contrast power or endpoint correlation model; no exact finite-sample permutation analysis; no attrition mechanism beyond A01's 15% arithmetic; no recruitment capacity, human review, ethics/privacy approval, consent, or T1 authorization. Final-state mismatch, critical target error and missingness are not modeled as step-score categories. Nothing here establishes retention, transfer, a human effect, or T1 feasibility.

## Input and runtime freeze

Source/input hashes, local WSLc version, image digest, network isolation and requested resources are in `FREEZE.json`. The image is an already-local `python:3.12-slim`; no pull/build, Docker Desktop, GPU or network access is needed. CPU and memory enforcement are not claimed. The source, settings and decision gate are immutable after this freeze. Candidate and independent auditor each receive one invocation; zero retries. Any runtime failure is a terminal retained STOP.
