# User-anchored minimum worthwhile benefit — synthetic method rung T0

## H / T / D / C / U

**H:** A preregistered, monotone 50%-choice crossing estimator can recover heterogeneous synthetic thresholds within one dose interval, distinguish planner-boundary waiting from local processing, and fail closed for insufficient support or a correctness regression.

**T:** Generate a deterministic synthetic corpus with fixed planted participant thresholds, seeded 2% response lapses, ties and missing responses. Candidate and independent auditor run once each. Candidate estimates the first dose with at least 50% worthwhile choices, bracketed by the prior tested dose; missing/tied responses are excluded. Require at least 20 valid responses at every dose. A hard correctness failure is never eligible regardless of preference. A sparse stratum must remain UNKNOWN. The independent auditor recomputes all cells from raw records and checks exact output and planted lower-50th-percentile order-statistic containment (quantile convention explicit for even-sized samples). Eight output mutations are controls.

**D:** PASS_METHOD_SCOPED only if the boundary and local strata each return brackets containing their planted lower-50th-percentile order statistics, their separate dose-response records remain distinct, all bins have frozen minimum support, the correctness-regression stratum is ineligible, sparse support is UNKNOWN, the independent raw audit agrees, and all eight mutations are rejected. No human/user-value claim follows.

**C:** This intentionally simple crossing rule ignores richer psychometric models, participant/task random effects, response order and confidence intervals. Binary synthetic choices are easier than real paired judgments.

**U:** Synthetic records only. Does not estimate actual user thresholds, adoption, satisfaction, task performance, route effect, or an engineering-benefit cutoff. No human participants, GUI, model, task execution, or safety effect.

## Frozen sources and environment

- Intake main: `0eed302f7c2f821011154ce5d5ad23d6540d215d`.
- Issue: [#7411](https://github.com/Unjuno/agent-interface/issues/7411).
- Candidate/auditor source hashes and generated-input hash are in `SHA256SUMS`.
- Executed on Ubuntu WSL2 host CPU (Python version recorded in raw run metadata). Not in WSLc or Docker: current `wslc.exe` inventory PIDs 15924 and 49012 remain live with unknown owner, and ten unrelated native MCP workers are present. No container inventory/launch was repeated. This is a resource-safety deviation, not an equivalence claim.
- No WSL, Docker, WSLc, memory, swap, or `.wslconfig` setting was changed. No requested memory cap or memory benefit is claimed.
- The candidate ran once and emitted the retained `CANDIDATE.json`; a separate raw-only auditor ran once and emitted `AUDIT.json` (`PASS_METHOD_SCOPED`, 8/8 controls rejected). Candidate, audit, compilation, and diff-check exits were 0.

## Reproduction

From the repository root:

```sh
python3 research/analysis/benefit_threshold_7411_t0_20261005/generate.py
python3 research/analysis/benefit_threshold_7411_t0_20261005/candidate.py
python3 research/analysis/benefit_threshold_7411_t0_20261005/audit.py
```

Exact stdout, statuses, fixture, candidate output, auditor output, and hashes are retained beside this file. These are method checks only; T1 participant research remains gated on consent, ethics/privacy review and task selection.
