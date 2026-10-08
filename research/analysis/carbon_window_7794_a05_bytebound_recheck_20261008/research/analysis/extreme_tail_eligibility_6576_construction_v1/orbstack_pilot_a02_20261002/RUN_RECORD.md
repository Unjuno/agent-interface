# Issue #6576 OrbStack Docker pilot A02 — PASS, method-scoped

- Allocation: `EXTREME-TAIL-ELIGIBILITY-6576-ORB-PILOT-A02-20261002-01`.
- Preregistered before candidate invocation in `PREREGISTRATION.md`; final environment/source/input freeze in `FREEZE.json`.
- Repository source/current main at freeze: `a81614d975631b1c2d0ad78fe98e4e96ba20b93a`.
- Environment: OrbStack isolated Ubuntu 24.04.5 arm64 machine `agent-interface-6576-pilot-a02-20261002`, machine ID `01M3Y1S37AM8DWQQXF4QSYBRMB`; its own Docker Engine 29.1.3, daemon ID `f81dff85-dd18-4e24-8323-02bf426a81c9`. No shared OrbStack Engine or other task machine was used.
- Container image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, resolved as linux/arm64. Candidate and auditor each used `--pull=never --network=none --cpus=1 --memory=2g --memory-swap=2g`; source/input were read-only, output was separate and writable. Preflight observed container cgroup `cpu.max=100000 100000`, `memory.max=2147483648`, `memory.swap.max=0`, readonly source enforcement and successful output write. The outer machine cgroup was 2 CPU / 4 GiB, swap max 0; `/proc/swaps` listed host zram and disk swap, but the task cgroup could not use swap.
- Frozen case: `stationary_light_tail_a02`, seed 65761102, 4,000 train + 4,000 held-out exponential rows. Input SHA-256: `22f29a8b096d5403a34d631c0c72e44e2fc8604ed3dae4bf5d42bd32cda088b5`.
- Candidate invocation: 1/1, exit 0; stdout/stderr empty. Raw output: 849,494 bytes; SHA-256 `77f57ec48f6759775d3572ddbd5ff7ca6bedd59575fadfb2f6ecceb48600c8d4`.
- Independent raw-only auditor invocation: 1/1, exit 0; `PASS_METHOD_SCOPED PASS_RAW_ONLY cases=1 train=4000 holdout=4000`. Retries: 0.

## Observed pilot result

- Gate: `ELIGIBLE_REFERENCE`; 400 observed threshold exceedances; censor count 0; missing endpoints 0; block-median ratio 1.4660378073 (frozen limit 1.5); lag-1 tail-indicator correlation -0.00002778 (frozen absolute limit 0.10).
- Empirical training p95 2.99594867; maximum 9.26755232.
- Naive pooled and eligible-gated GPD p99 both 4.66633609. Held-out count was 42/4,000; exact 95% Clopper–Pearson interval [0.00757766, 0.01416671], which contains nominal 0.01.
- TailID-equivalent adjusted p99 was 4.58248133. Held-out count was 45/4,000; exact 95% interval [0.00821734, 0.01502472], which contains nominal 0.01.
- Pilot disposition: `PASS_PILOT_SCOPED` under its one-case rule. No comparative advantage is established: this single sample gives overlapping point predictions/uncertainty and does not validate TailID parity with pinned CRAN/R.

## Scope boundary

This is a successful containerized single-case synthetic pilot, not the formal six-case T0. It does not establish operating characteristics across negative controls, real release-delay calibration, physical endpoint validity, real stationarity, safety-deadline protection, a production false-alarm rate, or any worst-case/safety bound. The formal six-case candidate and auditor remain uninvoked (0/0); its original allocation remains separate and unconsumed. A01's earlier STOP is preserved unchanged.
