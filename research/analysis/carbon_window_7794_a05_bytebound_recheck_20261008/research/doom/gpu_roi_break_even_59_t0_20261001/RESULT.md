# #59 GPU ROI break-even diagnostic — STOP

Allocation `MAP01-ROI-BREAK-EVEN-59-GPU-20261001-01` is retained with disposition **`STOP_PROTOCOL_DEVIATION_RAW_UNAVAILABLE`**. This is not a scientific PASS or FAIL; the hypothesis remains **NOT_EVALUATED**.

## H / T / D / C / U

- **H:** Whether CUDA including host↔device transfers exactly matches the independent NumPy oracle and has a latency break-even for the declared ROI/batch cells. **Not evaluated:** the stdout was truncated before a durable raw record could be retained and independently audited.
- **T:** The exact frozen runner was invoked once during the short local RTX 3080 allocation and returned exit code 0. Immediately before it, the PowerShell gate attempted `$a.Trim()` on a null empty compute-app list. PowerShell emitted a non-terminating error and continued into the candidate, so the in-command fail-closed gate did not complete as specified. A separate read-only observation at 03:09:42 UTC showed 0% / 0 MiB, CUDA available, and no active sibling GPU experiment.
- **D:** Complete stdout was not durably captured; no raw SHA-256 can be reported. Auditor invocations: 0. The visible, partial tool display is rejected as raw evidence, regardless of the status/parity fields it showed. Disposition is STOP, not a scientific result. No retry or replacement is allowed under this allocation.
- **C:** Windows CPython 3.11.9, NumPy 2.4.6, PyTorch 2.5.1+cu121 / CUDA 12.1, RTX 3080 Laptop GPU. Post-release read-only check at 03:13:11 UTC showed 0% / 0 MiB and no compute-app rows; the GPU allocation is released. No model, container, game, GUI, input, network, or external effect was used.
- **U:** No accepted CPU/CUDA parity, GPU speedup, task efficacy, threat detection, safety, production suitability, or MAP01 conclusion. The prior #5118 result remains unchanged. The preregistration, freeze, runner, auditor, and exact failure chronology are preserved under this directory.

## Recovery boundary

Do not repeat or reconstruct the consumed one-shot output. A later study, if justified, needs a new allocation ID, a fresh fail-closed resource gate, output written to a durable raw file by the runner/launcher, and a new source freeze.
