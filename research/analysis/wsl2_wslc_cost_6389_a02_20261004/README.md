# Ubuntu WSL2 vs WSLc iteration-cost pilot — #6389 A02

Status: new successor preregistration; A01 remains terminal and unchanged.

A01's first invocation passed the native WSL2 candidate and independent audit,
then stopped before WSLc because its digest-presence check incorrectly expected
the concatenated string `python@sha256:<digest>` in a table that displays the
repository/tag and `sha256:<digest>` separately. The full STOP and native
first-outcome evidence remain at
[`A01`](../wsl2_wslc_cost_6389_a01_20261004/FIRST_OUTCOME.md). A02 corrects only
the lookup predicate in a fresh allocation; it reruns a complete paired block
and does not pool A01's native result or change its files.

## H / T / D / C / U

- **H:** For the same small finite standard-library workload, native Ubuntu
  WSL2 has lower median end-to-end candidate-plus-independent-audit wall time
  than Dockerless WSLc, with byte-identical outputs and the same audit result.
- **T:** Three sequential paired blocks, order N→W, W→N, N→W. Each arm stages
  identical frozen source bytes, runs the candidate once, and if it exits 0
  runs the independent raw-only auditor once in a fresh process. Windows-host
  external wall time includes runtime launch, source staging, candidate and
  auditor. Native Ubuntu/WSL2 Python 3.12.3; WSLc 3.0.1.0 and cached pinned
  linux/amd64 Python 3.12-slim/Python 3.12.14. Network disabled, source and
  stager read-only in WSLc, unique output mounts, one container at a time.
- **D:** `PASS_COST_SCOPED` requires all six candidate/audit pairs to exit 0;
  three candidate outputs byte-identical across arms and repeats; every audit
  to report 9/9 rows, no errors or unsafe admissions, and 4/4 mutation controls
  detected; and native median pair time at least 10% lower than WSLc. Exact
  outputs without the time threshold are `PASS_PORTABILITY_ONLY`. Integrity or
  audit mismatch is `FAIL`. Any failed source/main/runtime/idle gate before a
  candidate is `STOP`. No retry.
- **C:** The small workload may exaggerate container startup overhead; host
  load, WSL utility-VM accounting, Python patch and libc/userland differences
  confound performance. Three pairs are not a fleet estimate.
- **U:** No Docker comparison, peak-RSS or host-memory-pressure attribution,
  effective memory cap, OOM prevention, GPU/GUI/model, or repository-wide
  migration claim. Scope is this finite workflow only.

## Freeze and runtime

- Base main: `13bab54ea6d91978247ecc1b70e5060db752367a`.
- Successor parent: A01 evidence commit `5515fb15` (A01 itself remains STOP).
- Branch: `research/wsl2-wslc-migration-6389-a02-20261004`.
- Allocation: `6389-wsl2-vs-wslc-belief-replay-a02-20261004`.
- Source: unchanged current-main #5368 replay at
  `research/analysis/belief_external_drift_5368_t0_20261003/`.
- Shared staging/child runner: A01's frozen `stage_and_run.py`, SHA-256
  `e7c73bb63f59fd4b35fb11c52af89e0c551b1a677a795d4deb2776871477aa1c`.
- WSLc image:
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
  local image ID
  `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`.
- Native WSL2: Ubuntu 24.04, Python 3.12.3, glibc 2.39. WSLc Python 3.12.14.
  Candidate/auditor use standard library only. `--memory 512M` is merely a
  request; no memory enforcement claim is made.

Immediately before each WSLc candidate or audit, `measure.py` requires the
running-container list to be empty and the output of `wslc images --digests
--no-trunc` to contain both the digest token `sha256:<digest>` and expected
local image ID. It stops without invoking if either condition fails. This is a
momentary collision check, not a persistent resource reservation.

The one-shot output tree is exclusive-created under `formal/`; full commands,
timestamps, return codes, stdout/stderr, and external durations are retained in
`formal/events.jsonl`. The first failed gate is terminal. A01 output remains
separate and will not be combined with these measurements.
