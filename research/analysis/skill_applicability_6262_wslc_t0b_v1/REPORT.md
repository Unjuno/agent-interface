# Issue #6262 — WSL Podman CUDA successor result

Experiment `AI-6262-T0B-WSLC-GPU-20261002-01` was frozen separately from the original T0. The original fixture, candidate, and auditor were mounted read-only from PR #6289's head; all outputs were written to a new WSL directory. Source hashes matched the freeze before execution.

## Result

`PASS_CONTAINER_REPRODUCTION_SCOPED`. The pinned PyTorch `2.5.1+cu121` image ran under Arch Linux WSL2 / Podman 6.1.3 with `--network none` and NVIDIA CDI (`nvidia.com/gpu=all`). CUDA was available on the RTX 3080 Laptop GPU. The candidate ran once and exited 0, enumerating 4,096 subsets across 12 feasible cells and 23 pair projections. The separate pure-Python auditor ran once and exited 0: exact semantic reconstruction of 4,096/4,096 rows, 1,987 naive joint false promotions refused, wide claim refused, exact qualified `t01` narrow claim retained, and 4/4 frozen mutations rejected. Retries: 0. `podman ps -a` was empty after both disposable `--rm` runs.

The raw candidate JSON is 4,786,213 bytes. Raw auditor JSON and distinct candidate/auditor stdout/stderr are retained with the fixture copy and SHA-256 manifest. Candidate stdout reports the source fixture's original ID `AI-6262-T0-GPU-20261002-01`; the enclosing independent allocation ID is T0B. The immutable fixture was not edited to relabel the predecessor ID.

## Execution boundary and retained setup issues

- Image: `docker.io/pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`, linux/amd64, 5,957,950,181 bytes. Python 3.11.10, PyTorch 2.5.1+cu121, CUDA runtime 12.1.
- WSL2 kernel `6.18.40.1-microsoft-standard-WSL2`; NVIDIA driver 581.57; cgroup v2. Image was pulled before freeze; container runs had no network. No memory-enforcement or speedup claim.
- Before freezing, one environment-only GPU probe used the local image/config ID instead of the registry manifest digest and Podman rejected it (`manifest schema unsupported`). No candidate code ran during that probe. The registry digest was read from `podman image inspect`; the corrected CUDA smoke probe passed before freeze.
- Construction suite output shows 5/5 tests `OK`. Its wrapper wrote a blank exit-code file because of shell status-variable quoting, so its exact process exit status is not claimed; this did not affect either formally captured invocation's exit code.

This confirms only a local WSL Podman CUDA reproduction path for this small synthetic allocation. It does not establish Docker parity, GPU necessity or speed, real skill applicability, GUI correctness, safety, or product performance. The original #6262 result and #6289 files remain unchanged.

Repository validation: the first analytical-index check ran while this was a narrow sparse checkout and reported the expected-but-absent directories as stale. After expanding only this worktree's sparse scope to all `research/analysis` contents, `python research/analysis/check_index.py` passed with 373 retained result/failure directories indexed; `git diff --check` passed. The initial sparse-scope diagnostic is not presented as a repository defect or a scientific result.
