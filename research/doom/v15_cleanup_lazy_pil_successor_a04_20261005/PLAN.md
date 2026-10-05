# V15 lazy-Pillow import successor A04 — wrapper import closure

A03's audited STOP reached the compatibility shim, which imports `research.observation_gating.gui_suite`; that module inserts `research/real_apps_v1` and imports `real_app_suite_v1`. A04 expands only the materialized source roots to include the immediate Python modules from those two directories. A01–A03 remain unchanged. The source tree, candidate import relocation, seven test modules, runtime, and D rule are unchanged.

## H/T/D/C/U

- **H:** Moving the capture-only Pillow import into `Backend.snapshot()` allows the real fake-X wrapper composition path to import and run its bounded cleanup regressions without changing screenshot semantics on snapshot use.
- **T:** Freeze current main `b5be19963454ce5edafc945b78b100012952dd15`, PR #8094 head `d0aa8463a10abf04d1b40cb4f498fc0a659fb827`, and virtual merge tree `78b8636f08bef691944da8bb536437586f0d116a`. Materialize all immediate-child Python modules under `research/live_control`, `research/doom`, `research/observation_tiles`, `research/observation_gating`, and `research/real_apps_v1`; apply only the one import relocation; invoke the same seven unittest modules once normally and once with `-O` using bundled Python 3.12.14 / Pillow 12.3.0 / NumPy 2.3.5.
- **D:** PASS only if both runs complete the expected 47 tests with zero failures/errors and the source overlay contains only the frozen import relocation. Any other import failure is retained as STOP; a reached assertion failure is FAIL. No retries.
- **C:** The added roots cover every local path in the observed wrapper chain, including the GUI shim's real-app import. Runtime has expected third-party packages; fake Xlib setup is provided by the test fixture. If the helper imports attempt real X/application activity, stop before any such call.
- **U:** A PASS is synthetic regression evidence only on Windows CPython with Pillow installed. It cannot prove native X11, live threat response, application effect, Linux/container portability, latency or Issue #59 acceptance. Earlier STOP results remain intact.

This is ordinary local regression, not a formal allocation. No dependency installs, network, X server, GUI, game, model or physical input are permitted.
