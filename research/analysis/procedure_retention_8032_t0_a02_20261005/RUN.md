# Execution record

Frozen source and decision settings: `FREEZE.json`, main base `7a9398add78d9095e5a85a60d324513fc3c2a1e3`. Local WSLc client 3.0.1.0, kernel 6.18.40.1-1. Local image `python:3.12-slim`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, repository digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. No pull/build. Network disabled; package bind mount read-only; requested 1 CPU and 512M. The runtime warned that swap-limit capabilities/cgroup were unavailable; resource enforcement is not claimed.

Frozen candidate command (one invocation; `candidate_raw.json` is stdout):

```powershell
$mount = "type=bind,source=$((Get-Location).Path),target=/work,readonly"
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --mount $mount --workdir /work --entrypoint python python:3.12-slim -B run_candidate.py
```

Candidate exited 0; raw JSON is 34,230 bytes and contains 54 sensitivity cells. Candidate stderr and exit are retained separately.

Frozen independent raw-only audit command (one invocation; it does not import `power_model.py`):

```powershell
$mount = "type=bind,source=$((Get-Location).Path),target=/work,readonly"
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --mount $mount --workdir /work --entrypoint python python:3.12-slim -B audit_power.py
```

Auditor exited 0 and emitted `PASS_RAW_RECONSTRUCTION`, 54 cells, zero errors. Candidate/auditor stdout, stderr and exit records are preserved in this directory. No retry or restart.

The construction suite passed 5/5 in both normal and optimized modes on the host and in one WSLc construction-validation invocation. JSON parsing and Python byte-compilation passed on the host. `candidate_raw.json` plus `FREEZE.json` are the deterministic input/output record; `SHA256SUMS.txt` fixes all retained bytes.
