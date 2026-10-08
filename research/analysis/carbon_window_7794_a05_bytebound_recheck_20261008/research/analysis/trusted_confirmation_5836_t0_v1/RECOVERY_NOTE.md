# Issue #5836 T0 recovery note

This is an evidence-preservation integration of the original frozen source and its pre-candidate resource STOP. It does not execute or adjudicate the trusted-confirmation hypothesis.

## Retained allocation boundary

- Allocation: `TRUSTED-CONFIRMATION-5836-T0-DESKTOP-20261001-01`.
- Original source/STOP tip: `d41b4aea3a9b62436057f9f56ac24c1cdf706c4f`.
- Disposition: `STOP_RESOURCE_COORDINATION_BEFORE_CANDIDATE`; formal candidate invocations 0, formal auditor invocations 0; scientific outcome `NOT_EVALUATED`.
- Reason: the #5085 coordination record did not establish release of a separate shared OrbStack guest past its booked window. An empty Docker inventory was not sufficient evidence that shared host CPU was available. No container or guest was touched by this allocation.
- The two preceding native host construction calls in `PREFREEZE.md` / `pre_freeze_raw.json` are construction-only and are not formal results. A new attempt requires a fresh allocation and an explicit resource window.

## Local preservation checks for this PR

- `python3 -B -m unittest -v research.analysis.trusted_confirmation_5836_t0_v1.test_semantics` — 5/5 pass.
- `python research/analysis/check_index.py` — pass, 527 retained result/failure directories indexed.
- `python research/check_workspace_index.py --git-tree` — pass, 156 reachable top-level directories.
- `git diff --check` — pass.
- The first unittest command was invoked from the repository root with a package-local module name and failed module discovery; the corrected fully qualified command above passed. No allocation candidate or formal auditor entrypoint was run.
- `START_GATE_STOP.json` SHA-256: `7504a17a04b3e5d5ba28472476a6407d302b83246c4292d704a4ee9aa8b010fc` (preserved source file; no edits to original evidence).

## H / T / D / C / U boundary

The owning Issue #5836 remains authoritative for the hypothesis and planned trusted-path fixture. This retained STOP supplies no evidence for or against that hypothesis: the planned test did not start (T), so the decision rule was not applied (D). It records only the resource-coordination constraint (C); trusted human attention, native GUI behavior, model behavior, efficacy, and any formal result remain unobserved (U).
