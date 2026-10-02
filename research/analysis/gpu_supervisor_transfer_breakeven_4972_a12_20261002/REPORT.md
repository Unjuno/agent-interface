# Allocation 12 result — transfer-inclusive CPU/CUDA break-even

**Disposition: `PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED`.** The frozen CPU/CUDA contract and raw audit passed, but the RTX 3080 did not reach the preregistered 20% break-even threshold at any of the six batch sizes.

## H / T / D / C / U

- **H:** CUDA may reduce per-row decision latency by at least 20% at a preregistered batch size after transfers and the CPU-owned final gate are included.
- **T:** One fresh 1,024-row synthetic data set (256 each: fresh_valid, stale, ambiguous, forced_yield), seed `49720261012`; batch sizes 1, 4, 16, 64, 256, 1024; five warmups and 30 alternating CPU/CUDA pairs. One WSLc candidate and one separate CPU-only raw auditor ran in the assigned 11:40–11:55 UTC interval.
- **D:** Exact hint/admission parity, zero stale/ambiguous/forced-yield admissions, full raw timing reconstruction, source/data/image identity, and corruption controls were checked. No batch cleared CUDA p50 <= 80% of CPU p50 per row.
- **C:** One Windows laptop with RTX 3080 Laptop GPU, Arch Linux WSL2, WSLc 3.0.1.0, pinned PyTorch CUDA 12.1 image. This is a synthetic tiny-vector hint workload; configured container CPU/memory limits were requests, not proven enforcement.
- **U:** No claim about real model-call savings, natural batch distributions, task quality, GUI/input, production use, Docker removal, or other GPUs.

## Execution and audit

The candidate exited 0, emitted exactly one `candidate_result.json`, and reported Python 3.11.10, PyTorch 2.5.1+cu121, CUDA 12.1, and `NVIDIA GeForce RTX 3080 Laptop GPU`. Its raw JSON retains all 1,024 rows, six 30-pair timing series, pair order, hints, and admissions. The independent CPU-only auditor exited 0 with `PASS_CPU_AUDIT_SCOPED`, zero errors, and all five runtime corruption controls rejected. Construction checks also passed: dataset contract 3/3, full-auditor mutation tests 8/8, unsafe-admission tests 3/3. Candidate=1, CUDA candidate=1, auditor=1, retries=0.

| Batch | CPU p50 / row (ns) | CUDA end-to-end p50 / row (ns) | CUDA / CPU |
|---:|---:|---:|---:|
| 1 | 1,603.5 | 437,763.5 | 273.00× |
| 4 | 568.0 | 99,813.2 | 175.73× |
| 16 | 242.3 | 24,578.5 | 101.43× |
| 64 | 158.1 | 6,736.8 | 42.61× |
| 256 | 138.6 | 2,110.4 | 15.23× |
| 1,024 | 125.0 | 920.4 | 7.37× |

The GPU path includes Python list extraction, host tensor construction, host-to-device transfer, CUDA threshold computation, synchronization, device-to-host copies, and CPU admission. CUDA remained slower at every tested size. This supports keeping CPU for this synthetic hint; it does not establish the result for larger or learned computations.

## Runtime and procedure notes

The exact linux/amd64 image digest was already cached and matched local image ID `sha256:048a0de5d4322054f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32`. WSLc emitted `kernel does not support swap limit capabilities or the cgroup is not mounted`; effective memory/swap enforcement is not claimed. After completion, no WSLc containers were running and the RTX 3080 reported 0% / 0 MiB.

The host-side audit launcher expected a `candidate.exit.txt` receipt that had not been created, and PowerShell continued after its non-terminating read error. The prior candidate command had directly returned exit 0 and one result, which I verified before starting the single auditor; both exit receipts were then recorded from the direct command outputs. This wrapper defect is disclosed in `results/HOST_ORCHESTRATION_NOTE.md`. It did not modify frozen inputs or run either candidate or auditor twice.

Raw candidate, auditor receipt, combined stdout/stderr, exit receipts, start-gate snapshot, and post-run inventories are in `results/`; `results/SHA256SUMS` binds the evidence files. The frozen source, dataset, and protocol hashes are in FREEZE.json and SHA256SUMS. Historical allocation A11's main-mismatch STOP remains unchanged.
