# V15 lazy-Pillow import successor A03 — completed observed import closure

A02 retained an audited STOP: its 1,998-source closure passed the observation transport imports but omitted `research/observation_tiles/image_artifact.py`, which `session_v4` imports after adding that directory to `sys.path`. This A03 changes only the materialized-source closure by adding that exact module; the tested tree, candidate import relocation, test modules, runtime, and decision rule remain unchanged. A01 and A02 first outcomes are preserved.

## H/T/D/C/U

- **H:** Moving the capture-only Pillow import into `Backend.snapshot()` allows the seven fake-X per-key cleanup regression modules to import the actual wrapper chain and run without changing the existing snapshot capture semantics.
- **T:** Use virtual merge tree `78b8636f08bef691944da8bb536437586f0d116a` (main `b5be19963454ce5edafc945b78b100012952dd15` + PR #8094 head `d0aa8463a10abf04d1b40cb4f498fc0a659fb827`); materialize all immediate-child Python modules under `research/live_control` and `research/doom`, plus `research/observation_tiles/tile_transport.py`, `research/observation_tiles/image_artifact.py`, and `research/observation_gating/exact_gate.py`; apply only the same one-import relocation. In a new scratch root `C:\s15b`, run the exact seven-module suite once normal and once optimized with bundled CPython 3.12.14 / Pillow 12.3.0 / NumPy 2.3.5.
- **D:** PASS only if both runs complete 47 tests with no failures/errors and source diff is limited to the import relocation. Missing imports or any other setup error are STOP/FAIL as evidence supports; no retry.
- **C:** The closure now includes the exact missing `image_artifact` module whose only third-party import is Pillow, available in the frozen runtime. Other undeclared imports may still stop the run. No dependency install, Xlib, X server, GUI, game, model or input call is allowed.
- **U:** Any pass remains synthetic Windows runtime regression evidence only. It does not establish no-Pillow snapshot calls, Linux/container portability, native X11, live threat response, useful feedback, application effect, latency or Issue #59 completion. The earlier STOPs remain unchanged.

This is ordinary bounded regression work, not a formal allocation.
