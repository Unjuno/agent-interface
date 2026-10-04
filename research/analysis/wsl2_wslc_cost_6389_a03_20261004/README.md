# Ubuntu WSL2 vs WSLc iteration-cost pilot — #6389 A03

Status: fresh successor preregistration; A01 and A02 remain terminal, unchanged.

A01 stopped after one native candidate/auditor pair when a false-negative image
gate stopped before WSLc. A02 corrected that gate but stopped before any
candidate when main advanced after freeze. Their reports remain immutable:
[`A01 STOP`](../wsl2_wslc_cost_6389_a01_20261004/FIRST_OUTCOME.md) and
[`A02 STOP`](../wsl2_wslc_cost_6389_a02_20261004/FIRST_OUTCOME.md). A03 fixes
the image predicate and freezes against current main `2ed11c5552956499454e8a99acf5a2f374106d34`.
It will run a complete fresh comparison; it does not pool or reuse A01/A02
outputs or timings.

## H / T / D / C / U

- **H:** For this exact small standard-library workflow, native Ubuntu WSL2
  has lower median end-to-end candidate-plus-independent-audit wall time than
  Dockerless WSLc, with identical candidate outputs and audit results.
- **T:** Three fresh sequential pairs in order N→W, W→N, N→W. Each arm stages
  the same frozen source bytes, runs the candidate once and—only after exit
  0—the independent raw-only auditor once in a fresh process. The same
  Windows-host orchestrator times the full CLI invocations, including runtime
  startup, staging, candidate and audit. Native Ubuntu/WSL2 Python 3.12.3;
  WSLc 3.0.1.0, cached pinned linux/amd64 Python 3.12-slim/Python 3.12.14.
  Candidate/audit network none; WSLc source and stager read-only, separate
  output mounts, requested one CPU. Before each WSLc call it requires zero
  running WSLc containers and verifies the exact image digest plus local image
  ID from read-only inventory output.
- **D:** `PASS_COST_SCOPED` requires all six pairs exit 0; every candidate
  output is byte-identical across both arms and repetitions; each independent
  audit is 9/9 with zero errors/unsafe admissions and 4/4 mutation controls
  detected; and native median pair time is at least 10% lower than WSLc.
  Exact portability without the cost threshold is `PASS_PORTABILITY_ONLY`.
  Mismatch is `FAIL`; any source/main/runtime/idle failure before candidate is
  `STOP`. No retry.
- **C:** This small workload can exaggerate startup overhead; background load,
  Python patch, libc/userland and utility-VM accounting remain confounders.
  Three repetitions are not a fleet distribution.
- **U:** No Docker comparison, peak-RSS or host-pressure attribution, effective
  memory cap, OOM prevention, GUI/model/GPU, or repository-wide migration
  conclusion. This applies only to this finite workflow.

## Frozen source/runtime

- Main: `2ed11c5552956499454e8a99acf5a2f374106d34`.
- Parent A02 evidence commit: `2130ab7d` (A02 STOP is not changed).
- Branch: `research/wsl2-wslc-migration-6389-a03-20261004`.
- Allocation: `6389-wsl2-vs-wslc-belief-replay-a03-20261004`.
- Source: `research/analysis/belief_external_drift_5368_t0_20261003/`.
- Shared frozen source-staging child runner: A01
  `stage_and_run.py`, SHA-256
  `459034c71a1ece158b532141ebe79e20b88f07f6f02eb576c223a15a62d43dea`
  (materialized Windows checkout bytes; Git blob
  `ea78550d3de9cf8bf9d35fd3c6f42427e745fbfb`).
- WSLc image:
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
  local image ID
  `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`.
- Ubuntu WSL2 Python 3.12.3/glibc 2.39; WSLc Python 3.12.14. Standard
  library only. `--memory 512M` is a request, not a proven limit.

`formal/` is exclusive-created by the single measurement invocation. It logs
both WSLc inventory command/output receipts and every runtime command, exit,
stdout/stderr, UTC time and external duration. A failed gate is terminal; A03
does not retry.
