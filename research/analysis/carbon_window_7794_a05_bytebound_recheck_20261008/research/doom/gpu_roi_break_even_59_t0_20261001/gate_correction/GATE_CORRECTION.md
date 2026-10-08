# GPU resource preflight correction — construction-only

This addendum addresses the PowerShell null-list defect that caused allocation `MAP01-ROI-BREAK-EVEN-59-GPU-20261001-01` to continue after a preflight error. It does not amend that consumed allocation, its freeze, or its STOP disposition.

## H / T / D / C / U

- **H:** Empty/null `nvidia-smi` compute-app output is treated as an empty inventory; any active process, nonzero/unparseable GPU snapshot, or failed query is STOPped.
- **T:** Pure fixture-driven PowerShell gate test; no CUDA kernel, GPU tensor, model, or candidate benchmark is run. Eight cases cover null, empty, whitespace, active process, nonzero utilization, malformed utilization, and each query-command failure.
- **D:** `pwsh -NoLogo -NoProfile -File .\test_gpu_preflight_gate.ps1` — **8/8 passed**. The corrected gate was also run read-only against the current host and returned `PREFLIGHT_OK`, 0%, 0 MiB, compute-app count 0. That snapshot is not an allocation or lease.
- **C:** PowerShell 7.6.5 on Windows; fixture tests only. No Docker/OrbStack, GUI, game, model, or external effect.
- **U:** Construction evidence only. It does not restore the lost raw output, audit the prior candidate, qualify GPU availability, authorize a new allocation, or establish CUDA/CPU parity or speedup.

## Exact files

- `gpu_preflight_gate.ps1` Git blob `4d7fcff86b6be2e1e8f751d8c8065826a937b96d`, SHA-256 `293663EE55099E1C56640453E291C8BB88307A688C84F0DB2361BE84957CE79A`
- `test_gpu_preflight_gate.ps1` Git blob `4f5ce288bd6f285c1857b8351053b9f5cbb363f8`, SHA-256 `7398327151D154CEC9FFBE3708594C4E4F82DD99A37200D63AFC971615D0B3CB`

These files are additive; the frozen benchmark, auditor, PREREGISTRATION, FREEZE, STOP and RESULT remain unchanged. Any future GPU measurement requires a fresh allocation ID and freeze with durable raw-file output.
