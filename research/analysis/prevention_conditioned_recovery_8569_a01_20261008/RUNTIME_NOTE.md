# Runtime and construction provenance

- WSL CLI: `3.0.1.0`; Ubuntu distribution; Python `3.12.3`; Linux kernel `6.18.40.1-microsoft-standard-WSL2`.
- The local WSLc Python image was present as `python:3.12-slim`, local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, RepoDigest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- A non-scientific WSLc `python3 --version` launcher preflight returned generic `E_FAIL` (exit 1). No candidate or auditor ran inside that preflight. Runtime switched to the already available Ubuntu/WSL Python; this did not block the experiment.
- WSL snapshot before formal run: `/proc/self/cgroup` was `0::/non-systemd`; `free -h` reported 5.8 GiB total, 704 MiB used, 5.1 GiB free, 5.1 GiB available, and 2.0 GiB swap with 112 KiB used. This is host/WSL context only. No per-process memory cap or container enforcement is claimed.
- Construction test first exposed test-code conversion of exact fraction strings via `float("n/d")`; assertions were corrected to compare `Fraction` values. The subsequent pre-freeze construction run passed all five tests in 0.002 s. Neither construction run generated the formal candidate artifact or consumed the one-shot formal invocation.
- The experiment uses deterministic standard-library rational arithmetic, one process/CPU, and only the authored fixture. WSLc failure is preserved as infrastructure context; it does not alter the experiment's scientific disposition.
