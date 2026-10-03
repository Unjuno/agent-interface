# WSLc retained-evidence audit portability — Issue #6975

**Status before formal run:** FROZEN_PRE_FORMAL. Candidate invocations: 0/0. WSLc auditor invocations: 0/1. Retries: 0.

This is an audit-only successor to the environment STOP recorded on [Issue #5309](https://github.com/Unjuno/agent-interface/issues/5309). It does not rerun the original T6 candidate or revise any earlier result. The prior stop occurred under the CodexSandboxOffline profile before a container launched; this new run uses the current Windows/WSLc environment.

## H / T / D / C / U

- **H:** The unchanged T6 independent auditor can re-check the exact retained synthetic raw in a Dockerless WSLc container and reproduce its 432-row verdict while source/raw mounts remain read-only and all writes are confined to one fresh output mount.
- **T:** Use main `42c86df0923aff536a1ee3a592b9fb74582891df`, raw Git blob `c85dc5cf32838e3ef7d63b0f57933a90bb66d59f` (SHA-256 `0b93411768024bd62f035422ec9bf613e15f89b905347c104f735aa45bf4847e`), and auditor Git blob `7333bdbd0e02df84a64161e773a261d53e76bb27` (SHA-256 `dce1416b4ca42e6bf0ef847aa9c4aa42a4e8fe415571401d683257cd97adbae5`). Use only cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, linux/amd64, Python 3.12.14), `--pull never --network none --cpus 1 --rm`, read-only source and dedicated writable output mounts. Run the existing auditor once with `python -B`; candidate=0, auditor=1, retries=0. The exact container command and frozen identities are in `FREEZE.json`.
- **D:** PASS_WSLC_AUDIT_PORTABILITY_SCOPED only if the unchanged auditor exits 0 and reports 432 rows, 432 unique cases, 432 independent row matches, semantic SHA-256 `a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193`, and failed-probe wrong-target counts 27 (task fallback) / 0 (yield fallback); pre/post source identities match; the independent host receipt verifier passes; and the uniquely named container is removed. Preserve any STOP/FAIL and do not retry.
- **C:** This is a replay of retained synthetic evidence, not a candidate run or a new scientific claim. Current WSLc `run --help` does not expose Docker read-only-rootfs or pids-limit options. The bounded substitute for this exact auditor is no network, an ephemeral container, read-only source bind, one dedicated output bind, and static review of the auditor. Rootfs isolation and general Docker flag parity are explicitly not claimed.
- **U:** No Docker/native-WSL comparison, end-to-end iteration improvement, peak-memory reduction, effective memory/swap cap, OOM safety, GUI/model/application effect, or product claim. Any timing and host/WSL memory or PSI readings are descriptive only; no memory pressure will be induced.

## Frozen source and runtime

- Host: Windows build 10.0.26200.9550; WSL package 3.0.1.0; kernel 6.18.40.1-1; Ubuntu remains WSL2; WSLc 3.0.1.0.
- Raw input: `research/experiments/dual_control_5309_t6/raw.json`, Git blob `c85dc5cf32838e3ef7d63b0f57933a90bb66d59f`.
- Auditor: `research/experiments/dual_control_5309_t6/audit.py`, Git blob `7333bdbd0e02df84a64161e773a261d53e76bb27`.
- Exact image metadata and command: `FREEZE.json`.

The retained auditor reads the raw JSON and emits its audit result to stdout. It does not write to source; `python -B` disables bytecode writes, and stdout is redirected to the unique output mount.

## Migration boundary

WSLc was selected because it is available on this host without Docker Desktop. The run deliberately omits `--read-only` and `--pids-limit`: the installed WSLc CLI does not expose those Docker options. It also omits `--memory`; prior evidence shows accepted WSLc memory settings are not a proven hard cap on this host. This one audit can demonstrate the bounded Dockerless path only, not that the whole repository or every Docker workflow is migrated.

Hosted CI, frozen runtime allocations, WSL global configuration, other containers, Docker installation/startup, and `wsl --shutdown` are out of scope. See [#3352](https://github.com/Unjuno/agent-interface/issues/3352) and the [WSLc local runtime guide](https://github.com/Unjuno/agent-interface/blob/main/.github/wslc-local-containers.md).

