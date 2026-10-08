# T0 execution record

- Freeze: main `0eed302f7c2f821011154ce5d5ad23d6540d215d`; Issue #7411 T0; unique branch `research/7411-user-benefit-t0-20261005`.
- Environment: Ubuntu WSL2, Linux `6.18.40.1-microsoft-standard-WSL2`, Python `3.12.3`, x86_64. Synthetic workload only.
- Container readiness: `wslc.exe` exists and `wslc info` responds, but old inventory processes PIDs 15924/49012 were confirmed still live with unknown owner. Ten unrelated `native_mcp_v1.py` workers were visible in the distro. No container query/start, Docker daemon, GUI, GPU, or WSL configuration was touched. A container run was avoided to prevent colliding with the unresolved shared inventory; this CPU-only T0 does not require container semantics.
- Commands, in order, each run once for the T0: `python3 research/analysis/benefit_threshold_7411_t0_20261005/generate.py`; `python3 research/analysis/benefit_threshold_7411_t0_20261005/candidate.py > research/analysis/benefit_threshold_7411_t0_20261005/CANDIDATE_STDOUT.txt`; `python3 research/analysis/benefit_threshold_7411_t0_20261005/audit.py`.
- Generator: exit 0; 1,230 synthetic records, seed 7411. Exact stdout and input hash retained.
- Candidate: exit 0; output byte-identical to retained `CANDIDATE_STDOUT.txt`; SHA-256 `c7637d91cb12511bdece9d4e4eb65e8a665f675841867ff3e89f3bf63d2d101a`.
- Independent auditor: exit 0; `PASS_METHOD_SCOPED`, 4 strata verified, 8/8 corruption controls rejected. `AUDIT.json` retains the receipt.
- Candidate brackets: planner-boundary `[100,150]` ms contains planted lower-50th-percentile order statistic 100; local-processing `[150,200]` ms contains planted lower-50th-percentile order statistic 150; correctness-regression `INELIGIBLE_CORRECTNESS_GATE`; sparse-support `UNKNOWN_INSUFFICIENT_SUPPORT`.
- `py_compile` for all three scripts and `git diff --check` both exited 0 after the candidate/auditor invocations. These checks do not rerun the candidate or auditor.
- Scope: synthetic method behavior only. No preference or threshold from people, no route-efficacy measurement, no task/safety evidence, and no memory or timing benefit from WSL2 versus WSLc.
