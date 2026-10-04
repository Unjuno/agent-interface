# Ubuntu WSL2 vs WSLc iteration-cost pilot — #6389 A01

Status: preregistration; no formal candidate has run.

This is an additive new runtime-comparison allocation under #6389. It reuses
the current-main finite #5368 external-transition replay as a workload, but it
does not repeat or replace its scientific result or the older WSLc portability
allocation. The question here is whether native Ubuntu WSL2 lowers one complete
edit-run-audit iteration cost relative to Dockerless WSLc while preserving the
same current-main outputs.

## H / T / D / C / U

- **H:** On this exact small, standard-library CPU workflow, native Ubuntu
  WSL2 has a lower median end-to-end candidate-plus-independent-audit wall time
  than WSLc, with byte-identical outputs and the same independent audit result.
- **T:** Three sequential paired blocks, alternating order N→W, W→N, N→W.
  Each arm stages the exact same frozen source bytes, invokes the candidate
  once, then the independent raw-only auditor once in a fresh process. The
  native arm uses Ubuntu WSL2/Python 3.12.3; WSLc uses the locally cached,
  digest-pinned Python 3.12-slim image/Python 3.12.14. Both have networking
  disabled for candidate execution; WSLc source mounts are read-only, outputs
  are distinct writable paths, and no Docker/Podman/GPU/model/GUI/input is used.
  The same Windows-host orchestrator times the complete two-stage invocation
  for each arm. Source-copy/runner/auditor wrapper overhead is included.
- **D:** `PASS_COST_SCOPED` only if all six candidate/audit pairs exit 0, each
  candidate's three outputs match byte-for-byte across arms and repetitions,
  every auditor independently reports 9/9 rows, zero errors, zero unsafe
  admissions and 4/4 mutation detections, and the native median end-to-end
  iteration is at least 10% lower than WSLc with no correctness regression.
  Exact outputs without the cost threshold are `PASS_PORTABILITY_ONLY`; any
  integrity/audit mismatch is `FAIL`; an unavailable runtime, parity, or
  ownership gate before candidate is `STOP`.
- **C:** Workload is deliberately small and may exaggerate container startup
  cost; background host load, utility-VM accounting, differing Python patch
  versions and libc/userland remain confounders. Repetitions do not establish
  a stable fleet distribution.
- **U:** No Docker comparison, peak-RSS or host-memory-pressure attribution,
  effective memory-cap, OOM-prevention, GPU/GUI/model, or repository-wide
  migration claim. A scoped result applies only to this finite workload.

## Frozen inputs and runtime

- Base: current `main` `13bab54ea6d91978247ecc1b70e5060db752367a`.
- Branch: `research/wsl2-wslc-migration-6389-a01-20261004`.
- Allocation: `6389-wsl2-vs-wslc-belief-replay-a01-20261004`.
- Source: `research/analysis/belief_external_drift_5368_t0_20261003/`.
- Candidate and oracle source are pinned both by current Git blob IDs and by
  SHA-256 of the exact materialized bytes mounted/copied by both arms.
- WSLc image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
  (`linux/amd64`, local image ID
  `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`).
- WSL software/WSLc 3.0.1.0; Ubuntu 24.04 on WSL2, Python 3.12.3, glibc
  2.39. WSLc Python is 3.12.14. No dependency beyond the Python standard
  library is used by the candidate/auditor.
- The WSLc engine was idle at the final preflight; existing stopped containers
  and all images were left untouched. The locally cached generic Python image
  was inspected read-only and is invoked with `--pull never`.

## Execution and preservation

The one-shot `measure.py` creates a new formal output tree exclusively, checks
the source hashes immediately before use, performs the frozen paired order,
records full commands/stdout/stderr/exits and external wall durations, and
halts on the first failed gate. No retry is permitted. `stage_and_run.py` copies
inputs to an ephemeral working directory and copies only the declared output
files to the separate result mount. The old #5368 outputs are read-only
references and are never overwritten.

Immediately before every WSLc invocation, the orchestrator requires the running
container list to be empty and confirms the pinned image is already cached; it
stops before candidate/auditor on either failure. This is a momentary collision
gate, not a reservation or proof of future host idleness.

The requested `--memory 512M` is not treated as a hard cap: WSLc has previously
reported unsupported swap/cgroup memory-limit capabilities on this host.
No pressure test is authorized or performed.
