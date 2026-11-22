# Current-main Docker/Linux public MCP contract R01

**Disposition: HOLD for the combined optimized run; scoped contracts pass when isolated.**

The code was not changed in this packet. Current-main runtime sources were mounted read-only into an existing, locally cached Linux image, with container networking disabled.

## Frozen environment

- Main baseline: `d18eefdb558d8292649f235d61a22bcd5a4e1b53`.
- Runtime tree: identical to `origin/main` at first read; image mounts this repository read-only at `/workspace`.
- Image: `issue57-calc-appserver-r88:local`, `sha256:a3b2b4cd54ca731a86f8d2ba16f1eb833220122c60bfafbdb048e5ad39e50056`; CPython 3.11.2, MCP/Xlib/ViZDoom, Xvfb/Openbox/xauth.
- Docker Desktop 29.8.1; `--network none`; all runs use ephemeral `--rm` containers. No sibling container, WSLc allocation, real game target, GUI, model, or provider call.
- Target modules: `runtime.cli_v1.test_mcp_server` and `runtime.cli_v1.test_mcp_guarded`.

## Results

| Run | Result |
|---|---|
| Both modules, normal | 87/87 passed in 96.444 s |
| Both modules, `-O` | **FAIL**: 86/87; `test_cancelled_transport_keeps_worker_and_receipt_without_replay` did not observe its dispatch worker's entry event within the frozen 2 s wait; 13.725 s total |
| Failing case alone, `-O` | 1/1 passed in 0.035 s |
| `test_mcp_server` alone, `-O` | 31/31 passed in 2.165 s |
| `test_mcp_guarded` alone, `-O` | 56/56 passed in 2.263 s |

The isolated runs narrow the failure to combined-suite context/timing, but do not erase the combined FAIL or prove its cause. No assertion, timeout, or acceptance condition was altered and the combined suite was not retried.

## Limits and next step

This is a current-main Linux public-MCP contract qualification with a recorded combined-suite HOLD. It does not establish live input, task outcome, release/recovery reliability, provider accounting, MAP01, Research Preview graduation, or distributable-runtime acceptance. Investigate why this single event-boundary test crosses its 2 s budget only in the combined optimized run before claiming the Linux `-O` suite is qualified.

Raw stdout/stderr and exit codes are retained in `raw/`. `source_hashes.json` identifies the exact test/code blobs; `SHA256SUMS` verifies the retained evidence packet.
