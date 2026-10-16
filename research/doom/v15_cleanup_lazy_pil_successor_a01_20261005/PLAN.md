# V15 cleanup regression successor — lazy capture dependency

This is a new bounded ordinary regression check after the prior frozen WSLc attempts stopped because the pinned image lacked Pillow. It uses the exact latest-main + PR #8094 virtual merge source as of the freeze and one source-only change: move `from PIL import ImageGrab` from module scope into `Backend.snapshot`, immediately before the existing capture call. No other code or test changes are allowed in the candidate overlay.

## H/T/D/C/U

- **H:** Deferring the capture-only Pillow import until `snapshot()` allows the existing batch-composition and per-key fake-X regression suite to import and exercise its fake backend without Pillow being needed at module initialization; screenshot behavior remains unchanged when `snapshot()` is called with Pillow installed.
- **T:** Materialize source from virtual merge tree `78b8636f08bef691944da8bb536437586f0d116a` (main `b5be19963454ce5edafc945b78b100012952dd15` + PR #8094 head `d0aa8463a10abf04d1b40cb4f498fc0a659fb827`), apply only the one-line import relocation, and run once normal and once optimized the exact seven-module suite in `RUN_PLAN.json`. Use the desktop-bundled CPython 3.12.14 / Pillow 12.3.0, network-free local process, and fake-X tests. No Xlib install, X server, GUI, game, model, or input calls.
- **D:** PASS only if both runs complete all 47 tests with zero failures/errors, and a source diff check confirms only the import moved into `snapshot()` immediately before its existing use. Any other exception or mismatch is retained as FAIL/STOP without rerun. This is a candidate regression result, not an acceptance result for live control.
- **C:** The prior failure may have reflected only the missing dependency at module import. Alternative: the suite may require additional unavailable modules or invoke capture unexpectedly; then the lazy import will not resolve the environment boundary. The bundled Python has Pillow 12.3.0; Xlib is absent and must remain unused.
- **U:** Passing establishes only ordinary synthetic test compatibility under this Windows CPython runtime with Pillow installed. It does not prove behavior without Pillow when `snapshot()` is called, Linux/container portability, native X11 behavior, application effect, live threat response, timing, or Issue #59 completion. The prior WSLc STOP remains unchanged.

## Frozen execution boundary

Exact runtime: `C:\Users\junny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`, Python 3.12.14, Pillow 12.3.0, Windows AMD64. No dependencies will be installed. The prior WSLc image is not reused. Each candidate mode is invoked once; no retry or source repair follows a result.
