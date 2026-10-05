# V15 lazy-Pillow import successor A02 — expanded import closure

A01 (same hypothesis, same candidate edit and seven regression modules) stopped after 47 discoveries because its materialized test source roots omitted the package `research.observation_tiles`, which the existing `research/live_control/tile_transport.py` imports through the batch wrapper chain. Its STOP and raw outcomes are retained unchanged at `v15_cleanup_lazy_pil_successor_a01_20261005/` and independently audited 9/9. This A02 is a new construction successor whose only delta is a complete, explicit source import closure.

## H/T/D/C/U

- **H:** Moving the capture-only Pillow import into `Backend.snapshot()` lets fake-X regression imports and wrapper composition proceed without Pillow being required at module initialization; the normal screenshot path retains the same import and call when invoked.
- **T:** From current main `b5be19963454ce5edafc945b78b100012952dd15` + PR #8094 head `d0aa8463a10abf04d1b40cb4f498fc0a659fb827`, materialize all immediate-child Python modules under `research/live_control` and `research/doom`, plus the exact transitive package modules `research/observation_tiles/tile_transport.py` and `research/observation_gating/exact_gate.py`. Apply only the same one-import relocation. Run once each in normal and optimized modes the exact seven-module suite in `RUN_PLAN.json` using the desktop Python 3.12.14/Pillow 12.3.0 runtime. Separate scratch root `C:\s15a`; network and package install unused.
- **D:** PASS only if both modes run all 47 expected tests with zero failures/errors and the source overlay changes only the frozen import location. Missing dependencies or any other setup error are STOP/FAIL as appropriate; preserve first result and do not retry.
- **C:** A01 identified the immediately missing observation-tiles package. This bounded closure includes its local `exact_gate` import and relies on bundled NumPy 2.3.5; further unresolved dependencies remain possible. Another STOP does not justify altering this A02 run after execution.
- **U:** Even a pass is synthetic regression evidence only under Windows CPython with Pillow present. It does not establish native X11, Linux/container portability, application effect, threat detection, latency, or Issue #59 completion. The A01 and WSLc STOP results remain unchanged.

This is ordinary local regression work, not a formal allocation. It makes no game, model, GUI, X server, native input, or external dependency-install calls.
