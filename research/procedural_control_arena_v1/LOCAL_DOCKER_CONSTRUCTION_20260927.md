# Local Docker construction rung — 2026-09-27

Issue: [#4695](https://github.com/Unjuno/agent-interface/issues/4695)  
Scope: verify that the landed Arena v1 mechanics and all nine Tk renderers execute in a local Linux Docker container. This is construction evidence only; it is not a Plain-vs-Agent-Interface comparison or benchmark-retention result.

## H / T / D / C / U

- **H:** The committed Arena v1 engine/tests/renderers can run in a small Linux container with Tk/Xvfb on the user's PC.
- **T:** Fetch the four source files at frozen main commit `f5205f532b1f64b71c9a1d69af07e8389f7fd8e0`; install `python3-tk xvfb xauth`; run unit tests, all renderer smoke checks, and bytecode compilation. No source edits or retries of tests.
- **D:** PASS only if all commands exit 0, 14 unit tests pass, and all 9 renderer checks pass.
- **C:** This does not test a rich model, Agent Interface, external evaluator isolation, paired episodes, timing frontiers, or held-out generalization.
- **U:** Whether this setup supports a model-in-loop controller and whether Arena results predict real-app behavior remain unknown.

## Frozen execution

- Host: Windows PC, Docker Engine **29.8.0**, Linux containers, WSL2 kernel `6.6.114.1-microsoft-standard-WSL2`.
- Container image reference: `python:3.11-slim`, resolved locally to `sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9` (`linux/amd64`). Debian packages were installed inside the disposable container; no image was committed.
- Runtime: Python `3.11.16`; Tkinter available.
- Source fetched by HTTPS from the frozen commit into `/tmp/arena-v1`; output JSON and combined raw command log were written to a host-mounted scratch directory.
- Source SHA-256:
  - `engine.py`: `cb33a008a6c9f05d37026826fd1241c86a555be0168211122fa926e9e16cb148`
  - `arena.py`: `a8f5a5e60d5076daf991af3ae074a052b2c2c1d6b145d6bef0d097c79a02dabb`
  - `test_engine.py`: `ced5c94425f6874fb7944f1b6cb88a30188ea3111b55cc00d62aacec7bb3b8ce`
  - `gui_smoke.py`: `988ee66ae5776c56f19b4104c5af6682b33b95bd747a4e7ac84de7f6b759693d`

Commands, each run once in the container:

```text
python3 -m unittest -v test_engine.py
xvfb-run -a python3 gui_smoke.py
python3 -m py_compile engine.py arena.py test_engine.py gui_smoke.py
```

## Raw outcome

```text
Ran 14 tests in 0.088s
OK
GUI_SMOKE_PASS 9
all three commands EXIT=0
```

The independent check here is limited to reconciling the process exit codes, test count, GUI smoke marker, source digests, and the mounted result/log files against the frozen manifest. It does not independently reimplement the Arena scorer.

**Decision: PASS for local Docker construction feasibility; HOLD for Issue #4695.** No GPU was used or needed for this mechanics rung. No model-performance claim is made. The Issue's paired B0/C1 run, evaluator isolation, axis frontier allocation, accounting, held-out evaluation, and cross-domain replication remain open.
