# Issue #5156 — local entrypoint/argv construction smoke

**Scoped result:** `PASS_LOCAL_ARGV_CONSTRUCTION_ONLY` for the T0 v2 successor. The first frozen T0 identity remains an immutable STOP and is included under `predecessor_t0_01/`; it is not overwritten or described as a scientific run.

## H / T / D / C / U

**H — Hypothesis.** Docker's configured command and entrypoint are distinct. For a Python image with `Entrypoint=null, Cmd=["python3"]`, supplying a `.py` path without an explicit interpreter replaces the default command and can fail before Python/preflight starts. Explicit `--entrypoint python3` with an argv-only script path should reach the interpreter and allow a dependency check before the harmless runner callback.

**T — Test.** On Docker Desktop 28.5.1, inspected the already-local pinned `python:3.12-slim` amd64 image. T0 v2 froze the exact `Entrypoint=null, Cmd=["python3"]` metadata, explicit `--entrypoint python3`, script path and arguments. Five construction tests ran before freeze. Candidate and raw-only auditor then each ran once in separate `--network=none`, read-only-source containers; only output was writable. T0 predecessor files preserve the initial misread/failure.

**D — Result.** T0 v2 construction tests: 5/5 PASS. Candidate's resolved process argv exactly matched the frozen command: `python3 /work/candidate.py --smoke-only --output /out/raw.json`; `sys.argv` matched exactly, the standard-library dependency preflight preceded one harmless smoke callback, and no formal runner, GUI, input, network, or model call occurred. Separate auditor: `PASS_LOCAL_ARGV_CONSTRUCTION_ONLY`, errors `[]`.

T0 predecessor: four construction tests passed, but its frozen metadata incorrectly swapped Entrypoint and Cmd. The sole attempted container invocation then returned `exec format error` before interpreter or candidate startup. No raw existed and no auditor ran. This is retained as an operator construction STOP; the T0 identity was not retried.

**C — Assumptions.** The local image is `linux/amd64`, not Allocation 04's `linux/arm64` Xvfb image. `json` is a standard-library stand-in for dependency-preflight sequencing, not Xlib. The callback is intentionally harmless and is not the owner runner.

**U — Limits / next evidence.** This validates only generic Docker/Python process-argv and preflight-order mechanics. It does not establish Xlib/Xvfb availability, physical key-up timing, input delivery, GUI task effects, or MAP01 behavior. Formal #5156 remains untested; it still needs a fresh exact-main, exact-image, explicit coordinator lease and the target-image Xlib preflight before any input. This local test does not inherit or consume the released OrbStack lane.

## Reproducibility and preserved records

- T0 v2 freeze: `FREEZE.json`; candidate `candidate.py`; input `cases.json`; raw `output/raw.json`; independent auditor `auditor.py`; audit `output/audit.json`.
- T0 v1 failed freeze and exact STOP: `predecessor_t0_01/FREEZE.json`, `STOP.json`, and `CORRECTION.md`; no raw was generated.
- Exact invocation vectors, source/image digests, and outcomes: `docker-invocations.txt`, `RUN_LOG.md`, and `SHA256SUMS.txt`.
- Candidate was invoked once for T0 v2; its auditor once. No X11/GUI/input, model, GPU, or network resource was used.
